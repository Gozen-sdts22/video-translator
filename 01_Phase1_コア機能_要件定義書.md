# Phase 1: コア機能 - 要件定義書

## 1. 概要

### 1.1 目的
動画から字幕を生成する基本パイプラインを実装する。

### 1.2 スコープ
- 音声抽出
- 文字起こし（日本語）
- 話者識別
- 翻訳（日本語→中国語）
- ASS形式出力
- 最小限のCLI/簡易UI

### 1.3 成果物
- 動作する基本パイプライン
- ASS形式の字幕ファイル出力

---

## 2. 機能詳細

### 2.1 音声抽出（audio_extractor.py）

#### 2.1.1 機能説明
FFmpegを使用して動画ファイルから音声トラックを抽出する。

#### 2.1.2 入力
| 項目 | 型 | 説明 |
|------|-----|------|
| video_path | str | 動画ファイルのパス |

#### 2.1.3 出力
| 項目 | 型 | 説明 |
|------|-----|------|
| audio_path | str | 抽出した音声ファイルのパス（WAV形式） |

#### 2.1.4 処理仕様

```python
def extract_audio(video_path: str, output_dir: str = None) -> str:
    """
    動画から音声を抽出する
    
    Args:
        video_path: 入力動画ファイルパス
        output_dir: 出力先ディレクトリ（省略時はtempディレクトリ）
    
    Returns:
        抽出した音声ファイルのパス
    
    処理:
        1. 出力パスを決定
        2. FFmpegコマンドを構築
        3. FFmpegを実行
        4. 出力ファイルの存在を確認
        5. パスを返す
    """
```

#### 2.1.5 FFmpegコマンド

```bash
ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {audio_path}
```

| オプション | 説明 |
|-----------|------|
| -vn | 映像を無効化 |
| -acodec pcm_s16le | 16bit PCM形式 |
| -ar 16000 | サンプリングレート16kHz（Whisper推奨） |
| -ac 1 | モノラル |

---

### 2.2 話者識別（diarizer.py）

#### 2.2.1 機能説明
pyannote-audioを使用して、音声中の話者を識別する。

#### 2.2.2 入力
| 項目 | 型 | 説明 |
|------|-----|------|
| audio_path | str | 音声ファイルのパス |

#### 2.2.3 出力
| 項目 | 型 | 説明 |
|------|-----|------|
| diarization_segments | List[dict] | 話者セグメントのリスト |

#### 2.2.4 出力形式

```python
[
    {"start": 0.5, "end": 3.2, "speaker": "SPEAKER_00"},
    {"start": 3.5, "end": 6.0, "speaker": "SPEAKER_01"},
    {"start": 6.2, "end": 10.1, "speaker": "SPEAKER_00"},
]
```

#### 2.2.5 処理仕様

```python
def diarize(audio_path: str, hf_token: str) -> List[dict]:
    """
    音声の話者識別を行う
    
    Args:
        audio_path: 音声ファイルパス
        hf_token: HuggingFaceトークン
    
    Returns:
        話者セグメントのリスト
    
    処理:
        1. pyannoteパイプラインをロード
        2. 音声ファイルを処理
        3. 結果をリスト形式に変換
        4. 返す
    """
```

#### 2.2.6 使用モデル

```
pyannote/speaker-diarization-3.1
```

---

### 2.3 文字起こし（transcriber.py）

#### 2.3.1 機能説明
Faster-Whisperを使用して、音声を日本語テキストに変換する。

#### 2.3.2 入力
| 項目 | 型 | 説明 |
|------|-----|------|
| audio_path | str | 音声ファイルのパス |
| initial_prompt | str | 認識精度向上のためのプロンプト（オプション） |

#### 2.3.3 出力
| 項目 | 型 | 説明 |
|------|-----|------|
| transcription_segments | List[dict] | 文字起こしセグメントのリスト |

#### 2.3.4 出力形式

```python
[
    {"start": 0.5, "end": 3.2, "text": "こんにちは、今日は天気がいいですね"},
    {"start": 3.5, "end": 6.0, "text": "お元気ですか？"},
]
```

#### 2.3.5 処理仕様

```python
def transcribe(audio_path: str, initial_prompt: str = None) -> List[dict]:
    """
    音声を文字起こしする
    
    Args:
        audio_path: 音声ファイルパス
        initial_prompt: 認識ヒント（アイドル用語等）
    
    Returns:
        文字起こしセグメントのリスト
    
    処理:
        1. Whisperモデルをロード
        2. 音声ファイルを処理
        3. セグメントをリスト形式に変換
        4. 返す
    """
```

#### 2.3.6 使用モデル・設定

```python
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe(
    audio_path,
    language="ja",
    initial_prompt=initial_prompt
)
```

#### 2.3.7 デフォルトinitial_prompt

```
推しメン、握手会、センター、チェキ、総選挙、ランキング、
メンバー、ファン、ライブ、コンサート、MV、楽曲
```

---

### 2.4 話者とテキストの紐付け（merger.py）

#### 2.4.1 機能説明
話者識別結果と文字起こし結果をマージし、各テキストに話者IDを付与する。

#### 2.4.2 入力
| 項目 | 型 | 説明 |
|------|-----|------|
| transcription_segments | List[dict] | 文字起こしセグメント |
| diarization_segments | List[dict] | 話者セグメント |

#### 2.4.3 出力
| 項目 | 型 | 説明 |
|------|-----|------|
| merged_segments | List[dict] | 話者付きセグメント |

#### 2.4.4 出力形式

```python
[
    {"start": 0.5, "end": 3.2, "text": "こんにちは", "speaker": "SPEAKER_00"},
    {"start": 3.5, "end": 6.0, "text": "お元気ですか？", "speaker": "SPEAKER_01"},
]
```

#### 2.4.5 処理仕様

```python
def merge_segments(
    transcription_segments: List[dict],
    diarization_segments: List[dict]
) -> List[dict]:
    """
    文字起こしと話者識別をマージする
    
    Args:
        transcription_segments: 文字起こしセグメント
        diarization_segments: 話者セグメント
    
    Returns:
        話者付きセグメント
    
    処理:
        1. 各文字起こしセグメントについて
        2. 時間的に最も重なる話者セグメントを探す
        3. 話者IDを付与
        4. 結果を返す
    """
```

#### 2.4.6 マッチングアルゴリズム

```python
def find_best_speaker(trans_seg, diar_segs):
    """重なり時間が最大の話者を返す"""
    best_speaker = "UNKNOWN"
    best_overlap = 0
    
    for d_seg in diar_segs:
        overlap_start = max(trans_seg["start"], d_seg["start"])
        overlap_end = min(trans_seg["end"], d_seg["end"])
        overlap = max(0, overlap_end - overlap_start)
        
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = d_seg["speaker"]
    
    return best_speaker
```

---

### 2.5 翻訳（translator.py）

#### 2.5.1 機能説明
Claude APIを使用して、日本語テキストを中国語に翻訳する。

#### 2.5.2 入力
| 項目 | 型 | 説明 |
|------|-----|------|
| segments | List[dict] | 話者付きセグメント |
| api_key | str | Claude APIキー |

#### 2.5.3 出力
| 項目 | 型 | 説明 |
|------|-----|------|
| translated_segments | List[dict] | 翻訳付きセグメント |

#### 2.5.4 出力形式

```python
[
    {
        "start": 0.5,
        "end": 3.2,
        "text": "こんにちは",
        "speaker": "SPEAKER_00",
        "translation": "你好"
    },
]
```

#### 2.5.5 処理仕様

```python
def translate_segments(
    segments: List[dict],
    api_key: str,
    batch_size: int = 10
) -> List[dict]:
    """
    セグメントを中国語に翻訳する
    
    Args:
        segments: 話者付きセグメント
        api_key: Claude APIキー
        batch_size: 1回のAPI呼び出しで処理する数
    
    Returns:
        翻訳付きセグメント
    
    処理:
        1. セグメントをバッチに分割
        2. 各バッチについてClaude APIを呼び出し
        3. レスポンスをパース
        4. 翻訳を各セグメントに付与
        5. 結果を返す
    """
```

#### 2.5.6 翻訳プロンプト

```
あなたはアイドルコンテンツの専門翻訳者です。
以下の日本語を中国語（簡体字）に翻訳してください。

ルール:
- 自然で流暢な中国語にする
- アイドル用語は適切に翻訳する（例: 推し→本命/推、センター→C位）
- 番号付きで出力する
- 翻訳のみ出力し、説明は不要

入力:
1. こんにちは
2. 推しメンが最高です

出力:
1. 你好
2. 我的本命最棒了
```

#### 2.5.7 バッチ処理

- 1回のAPI呼び出しで10〜20セグメントを処理
- 文脈を保つため連続するセグメントをまとめる
- APIエラー時はリトライ（最大3回）

---

### 2.6 ASS出力（ass_generator.py）

#### 2.6.1 機能説明
翻訳済みセグメントからASS形式の字幕ファイルを生成する。

#### 2.6.2 入力
| 項目 | 型 | 説明 |
|------|-----|------|
| segments | List[dict] | 翻訳付きセグメント |
| output_path | str | 出力ファイルパス |

#### 2.6.3 出力
| 項目 | 型 | 説明 |
|------|-----|------|
| ass_file | file | ASS形式の字幕ファイル |

#### 2.6.4 処理仕様

```python
def generate_ass(segments: List[dict], output_path: str) -> str:
    """
    ASS形式の字幕ファイルを生成する
    
    Args:
        segments: 翻訳付きセグメント
        output_path: 出力ファイルパス
    
    Returns:
        出力ファイルパス
    
    処理:
        1. ASSヘッダーを生成
        2. 話者ごとのスタイルを定義
        3. 各セグメントをDialogue形式に変換
        4. ファイルに書き込み
        5. パスを返す
    """
```

#### 2.6.5 ASS形式

```ass
[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SPEAKER_00,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1
Style: SPEAKER_01,Arial,48,&H0000FFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1
Style: SPEAKER_02,Arial,48,&H00FF8080,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1
Style: SPEAKER_03,Arial,48,&H008000FF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:03.20,SPEAKER_00,,0,0,0,,こんにちは\N你好
Dialogue: 0,0:00:03.50,0:00:06.00,SPEAKER_01,,0,0,0,,お元気ですか？\N你好吗？
```

#### 2.6.6 話者カラー定義

| 話者ID | 色 | ASSカラーコード |
|--------|-----|----------------|
| SPEAKER_00 | 白 | &H00FFFFFF |
| SPEAKER_01 | 黄 | &H0000FFFF |
| SPEAKER_02 | 水色 | &H00FF8080 |
| SPEAKER_03 | オレンジ | &H008000FF |

---

## 3. パイプライン統合（pipeline.py）

### 3.1 処理フロー

```python
def process_video(video_path: str, config: Config) -> str:
    """
    動画から字幕を生成するメインパイプライン
    
    Args:
        video_path: 入力動画ファイルパス
        config: 設定オブジェクト
    
    Returns:
        出力ASSファイルパス
    
    処理:
        1. 音声抽出
        2. 話者識別（並列可能）
        3. 文字起こし（並列可能）
        4. 話者とテキストのマージ
        5. カスタム辞書適用（Phase 4で実装）
        6. 翻訳
        7. ASS出力
    """
```

### 3.2 進捗コールバック

```python
def process_video(
    video_path: str,
    config: Config,
    progress_callback: Callable[[str, float], None] = None
) -> str:
    """
    progress_callback: (status_message, progress_ratio) を受け取る関数
    
    例:
        progress_callback("音声抽出中...", 0.1)
        progress_callback("文字起こし中...", 0.3)
        progress_callback("翻訳中...", 0.7)
        progress_callback("完了", 1.0)
    """
```

---

## 4. 設定（config.py）

### 4.1 設定項目

```python
@dataclass
class Config:
    # API設定
    claude_api_key: str
    hf_token: str
    
    # モデル設定
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    
    # 処理設定
    enable_diarization: bool = True
    translation_batch_size: int = 10
    
    # 出力設定
    output_dir: str = "./output"
    temp_dir: str = "./temp"
    
    # 初期プロンプト
    initial_prompt: str = "推しメン、握手会、センター..."
```

### 4.2 環境変数

```
CLAUDE_API_KEY=sk-ant-...
HF_TOKEN=hf_...
```

---

## 5. エラーハンドリング

### 5.1 例外クラス

```python
class SubtitleGeneratorError(Exception):
    """基底例外クラス"""
    pass

class AudioExtractionError(SubtitleGeneratorError):
    """音声抽出エラー"""
    pass

class TranscriptionError(SubtitleGeneratorError):
    """文字起こしエラー"""
    pass

class DiarizationError(SubtitleGeneratorError):
    """話者識別エラー"""
    pass

class TranslationError(SubtitleGeneratorError):
    """翻訳エラー"""
    pass
```

### 5.2 リトライ設定

| 処理 | リトライ回数 | 待機時間 |
|------|------------|---------|
| Claude API呼び出し | 3回 | 指数バックオフ（1s, 2s, 4s） |
| FFmpeg実行 | 1回 | - |

---

## 6. テスト要件

### 6.1 単体テスト

| テスト対象 | テスト内容 |
|-----------|-----------|
| audio_extractor | WAVファイルが正しく生成されるか |
| transcriber | テキストとタイムスタンプが取得できるか |
| diarizer | 話者セグメントが取得できるか |
| merger | 正しく話者が割り当てられるか |
| translator | 翻訳が取得できるか |
| ass_generator | 有効なASSファイルが生成されるか |

### 6.2 統合テスト

- 短い動画（1分）でパイプライン全体が動作するか
- 生成されたASSファイルがAegisubで開けるか

---

## 7. 依存パッケージ

```txt
# requirements.txt
faster-whisper>=1.0.0
pyannote.audio>=3.1.0
anthropic>=0.18.0
ffmpeg-python>=0.2.0
torch>=2.0.0
torchaudio>=2.0.0
```

---

## 8. 実装順序

1. `config.py` - 設定管理
2. `models/segment.py` - データモデル
3. `core/audio_extractor.py` - 音声抽出
4. `core/transcriber.py` - 文字起こし
5. `core/diarizer.py` - 話者識別
6. `core/merger.py` - マージ処理
7. `core/translator.py` - 翻訳
8. `utils/ass_generator.py` - ASS出力
9. `core/pipeline.py` - パイプライン統合
10. `app.py` - 簡易CLI/UI

---

## 9. 完了条件

- [ ] 動画ファイルを入力としてASS形式の字幕が出力される
- [ ] 日本語と中国語が両方表示される
- [ ] 話者ごとに色分けされている
- [ ] Aegisubで正しく開ける
- [ ] 単体テストがパスする
