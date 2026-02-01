# Phase 2: チェックAgent - 要件定義書

## 1. 概要

### 1.1 目的
AIによる品質チェック機能を追加し、誤認識や翻訳品質の問題を検出・修正提案する。

### 1.2 スコープ
- 誤認識チェック機能
- 翻訳品質チェック機能
- 一貫性チェック機能
- 修正提案の生成
- 辞書追加候補の検出

### 1.3 前提条件
- Phase 1が完了していること
- Claude APIが利用可能であること

### 1.4 成果物
- チェックAgent実装
- 修正提案データ構造
- パイプラインへの統合

---

## 2. 機能詳細

### 2.1 チェックAgent概要（checker.py）

#### 2.1.1 チェック観点

| チェック種別 | 説明 | 検出例 |
|-------------|------|--------|
| 誤認識チェック | 日本語テキストの不自然さを検出 | 「おしめん」→「推しメン」 |
| 翻訳チェック | 翻訳の品質・正確性を検出 | 意味の欠落、ニュアンス違い |
| 一貫性チェック | 用語・文体の統一性を検出 | 「ファン」と「オタク」混在 |

#### 2.1.2 処理フロー

```
翻訳済みセグメント
        │
        ▼
┌───────────────────┐
│ 誤認識チェックAgent │
│                   │
│ - 意味不明な文    │
│ - 文脈不一致      │
│ - アイドル用語    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 翻訳チェックAgent  │
│                   │
│ - 意味の欠落      │
│ - ニュアンス      │
│ - 用語の適切さ    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 一貫性チェックAgent│
│                   │
│ - 用語統一        │
│ - 文体統一        │
│ - 話者一貫性      │
└───────────────────┘
        │
        ▼
修正提案付きセグメント
```

---

### 2.2 データ構造

#### 2.2.1 修正提案（Suggestion）

```python
@dataclass
class Suggestion:
    id: int                   # 提案ID
    segment_id: int           # 対象セグメントID
    type: str                 # チェック種別
    field: str                # 対象フィールド
    original: str             # 元の値
    suggested: str            # 提案値
    reason: str               # 理由（日本語）
    confidence: float         # 信頼度（0.0-1.0）
    add_to_dict: bool         # 辞書追加候補フラグ
    dict_entry: dict | None   # 辞書エントリ候補
```

#### 2.2.2 type（チェック種別）

| 値 | 説明 |
|-----|------|
| `recognition` | 誤認識チェック |
| `translation` | 翻訳チェック |
| `consistency` | 一貫性チェック |

#### 2.2.3 field（対象フィールド）

| 値 | 説明 |
|-----|------|
| `text_ja` | 日本語テキスト |
| `text_zh` | 中国語テキスト |

#### 2.2.4 セグメントのstatus更新

```python
def determine_status(suggestions: List[Suggestion]) -> str:
    """
    提案に基づいてステータスを決定
    
    Returns:
        "ok": 提案なし
        "warning": 提案あり（信頼度0.5以上）
        "error": 重大な問題あり（信頼度0.8以上）
    """
```

---

### 2.3 誤認識チェック

#### 2.3.1 機能説明
日本語テキストの誤認識を検出し、修正を提案する。

#### 2.3.2 処理仕様

```python
def check_recognition(
    segments: List[Segment],
    api_key: str,
    batch_size: int = 20
) -> List[Suggestion]:
    """
    誤認識をチェックする
    
    Args:
        segments: チェック対象セグメント
        api_key: Claude APIキー
        batch_size: バッチサイズ
    
    Returns:
        修正提案リスト
    
    検出対象:
        - 意味不明な文（「あのそのえっと」の連続等）
        - 文脈に合わない単語
        - アイドル用語の誤認識
        - 固有名詞の表記揺れ
    """
```

#### 2.3.3 プロンプト

```
あなたはアイドルコンテンツの字幕校正専門家です。
以下の日本語テキストをチェックし、音声認識の誤りを指摘してください。

## チェック観点
1. 意味不明な箇所（フィラーの過剰認識など）
2. 文脈に合わない単語
3. アイドル用語の誤認識（例：「おしめん」→「推しメン」）
4. 固有名詞の表記揺れ

## 入力データ
{segments_json}

## 出力形式（JSON）
問題があるセグメントのみ出力：
[
  {
    "segment_id": 12,
    "original": "おしめんが最高です",
    "suggested": "推しメンが最高です",
    "reason": "「おしめん」は「推しメン」の誤認識と思われます",
    "confidence": 0.9,
    "add_to_dict": true,
    "dict_entry": {
      "wrong": "おしめん",
      "correct": "推しメン",
      "category": "アイドル用語"
    }
  }
]

問題がない場合は空配列を返してください: []
```

---

### 2.4 翻訳チェック

#### 2.4.1 機能説明
翻訳の品質をチェックし、改善を提案する。

#### 2.4.2 処理仕様

```python
def check_translation(
    segments: List[Segment],
    api_key: str,
    batch_size: int = 20
) -> List[Suggestion]:
    """
    翻訳品質をチェックする
    
    Args:
        segments: チェック対象セグメント
        api_key: Claude APIキー
        batch_size: バッチサイズ
    
    Returns:
        修正提案リスト
    
    検出対象:
        - 意味の欠落
        - ニュアンスの違い
        - アイドル用語の不適切な訳
        - 文化的なニュアンスの欠落
    """
```

#### 2.4.3 プロンプト

```
あなたはアイドルコンテンツの日中翻訳専門家です。
以下の翻訳をチェックし、改善点を指摘してください。

## チェック観点
1. 意味が正確に伝わっているか
2. アイドルファン向けの適切な表現か
3. ニュアンスの欠落がないか
4. 文化的な背景が適切に反映されているか

## 入力データ
{segments_json}

## 出力形式（JSON）
[
  {
    "segment_id": 14,
    "original": "想站在中心",
    "suggested": "想站C位",
    "reason": "「センター」は中国のアイドルファン向けには「C位」の方が自然です",
    "confidence": 0.85,
    "add_to_dict": false,
    "dict_entry": null
  }
]
```

---

### 2.5 一貫性チェック

#### 2.5.1 機能説明
字幕全体の用語・文体の一貫性をチェックする。

#### 2.5.2 処理仕様

```python
def check_consistency(
    segments: List[Segment],
    api_key: str
) -> List[Suggestion]:
    """
    一貫性をチェックする
    
    Args:
        segments: 全セグメント
        api_key: Claude APIキー
    
    Returns:
        修正提案リスト
    
    検出対象:
        - 同じ用語に異なる訳語
        - 文体（敬体/常体）の混在
        - 話者の不整合
    """
```

#### 2.5.3 プロンプト

```
あなたは字幕の品質管理専門家です。
以下の字幕全体の一貫性をチェックしてください。

## チェック観点
1. 同じ日本語に異なる中国語訳が使われていないか
2. 文体（敬体/常体）は統一されているか
3. 話者の区別は適切か

## 入力データ
{segments_json}

## 出力形式（JSON）
[
  {
    "segment_id": 25,
    "original": "粉丝",
    "suggested": "饭",
    "reason": "「ファン」の訳として、セグメント5では「饭」を使用しているため統一すべきです",
    "confidence": 0.7,
    "add_to_dict": false,
    "dict_entry": null
  }
]
```

---

### 2.6 チェック統合

#### 2.6.1 処理仕様

```python
class SubtitleChecker:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def check_all(
        self,
        segments: List[Segment],
        progress_callback: Callable = None
    ) -> Tuple[List[Segment], List[Suggestion]]:
        """
        全てのチェックを実行する
        
        Args:
            segments: チェック対象セグメント
            progress_callback: 進捗コールバック
        
        Returns:
            (更新されたセグメント, 全ての提案)
        
        処理:
            1. 誤認識チェック実行
            2. 翻訳チェック実行
            3. 一貫性チェック実行
            4. 提案をセグメントに紐付け
            5. ステータス更新
            6. 結果を返す
        """
```

#### 2.6.2 進捗コールバック

```python
# 進捗通知の例
progress_callback("誤認識チェック中...", 0.33)
progress_callback("翻訳チェック中...", 0.66)
progress_callback("一貫性チェック中...", 1.0)
```

---

## 3. API呼び出し設計

### 3.1 バッチ処理

| チェック種別 | バッチサイズ | 理由 |
|-------------|------------|------|
| 誤認識 | 20 | セグメント単位で独立して判断可能 |
| 翻訳 | 20 | セグメント単位で独立して判断可能 |
| 一貫性 | 全体 | 全体を見る必要があるため |

### 3.2 APIコスト見積もり

| 処理 | 入力トークン目安 | 出力トークン目安 |
|-----|----------------|----------------|
| 誤認識チェック（20セグメント） | 2,000 | 500 |
| 翻訳チェック（20セグメント） | 3,000 | 500 |
| 一貫性チェック（100セグメント） | 8,000 | 1,000 |

### 3.3 レスポンスパース

```python
def parse_check_response(response_text: str) -> List[dict]:
    """
    Claude APIのレスポンスをパースする
    
    処理:
        1. JSONブロックを抽出（```json ... ```）
        2. JSONをパース
        3. 必須フィールドの存在確認
        4. 結果を返す
    
    エラー処理:
        - JSONパースエラー → 空リストを返す
        - 必須フィールド欠落 → その項目をスキップ
    """
```

---

## 4. パイプライン統合

### 4.1 更新後のフロー

```python
def process_video(video_path: str, config: Config) -> ProcessResult:
    """
    更新後のパイプライン
    
    Returns:
        ProcessResult:
            segments: List[Segment]  # 全セグメント
            suggestions: List[Suggestion]  # 全提案
            ass_path: str  # ASSファイルパス
    """
    
    # Phase 1の処理
    audio_path = extract_audio(video_path)
    diarization = diarize(audio_path)
    transcription = transcribe(audio_path)
    segments = merge_segments(transcription, diarization)
    segments = translate_segments(segments)
    
    # Phase 2: チェックAgent
    checker = SubtitleChecker(config.claude_api_key)
    segments, suggestions = checker.check_all(segments)
    
    # ASS出力（暫定版、レビュー前）
    ass_path = generate_ass(segments, config.output_dir)
    
    return ProcessResult(segments, suggestions, ass_path)
```

### 4.2 ProcessResult

```python
@dataclass
class ProcessResult:
    segments: List[Segment]       # 全セグメント
    suggestions: List[Suggestion] # 全修正提案
    ass_path: str                 # 暫定ASSファイルパス
    stats: dict                   # 統計情報
```

### 4.3 統計情報

```python
stats = {
    "total_segments": 156,
    "segments_with_issues": 12,
    "suggestions_by_type": {
        "recognition": 5,
        "translation": 4,
        "consistency": 3
    },
    "dict_candidates": 3
}
```

---

## 5. 辞書追加候補

### 5.1 検出条件

チェックAgentが以下の条件を満たす修正を見つけた場合、辞書追加候補としてマーク：

1. 誤認識チェックで検出
2. パターンが明確（単語の置換）
3. 信頼度が高い（0.8以上）

### 5.2 候補データ

```python
dict_entry = {
    "wrong": "おしめん",      # 誤認識パターン
    "correct": "推しメン",    # 正しい表記
    "category": "アイドル用語" # カテゴリ
}
```

### 5.3 Phase 4との連携

- Phase 2では候補の検出のみ
- Phase 4で辞書への追加UIを実装

---

## 6. エラーハンドリング

### 6.1 APIエラー

```python
class CheckerError(SubtitleGeneratorError):
    """チェックAgent関連エラー"""
    pass

class RecognitionCheckError(CheckerError):
    """誤認識チェックエラー"""
    pass

class TranslationCheckError(CheckerError):
    """翻訳チェックエラー"""
    pass

class ConsistencyCheckError(CheckerError):
    """一貫性チェックエラー"""
    pass
```

### 6.2 エラー時の動作

| エラー種別 | 動作 |
|-----------|------|
| API一時エラー（429, 500） | リトライ（最大3回） |
| APIキー無効 | 処理中断、エラー通知 |
| レスポンスパースエラー | 該当チェックをスキップ、警告ログ |
| タイムアウト | リトライ、それでも失敗なら該当チェックスキップ |

### 6.3 部分的失敗の許容

- チェックの一部が失敗しても、他の結果は利用可能にする
- 失敗したチェックは統計情報に記録

---

## 7. テスト要件

### 7.1 単体テスト

| テスト対象 | テスト内容 |
|-----------|-----------|
| check_recognition | 既知の誤認識パターンを検出できるか |
| check_translation | 翻訳の問題を検出できるか |
| check_consistency | 不一致を検出できるか |
| parse_check_response | 各種レスポンスを正しくパースできるか |

### 7.2 統合テスト

- 全チェックが連続して実行できるか
- 提案がセグメントに正しく紐付くか
- エラー時に適切にスキップされるか

### 7.3 テストデータ

```python
# 誤認識テスト用
test_segments_recognition = [
    {"id": 1, "text_ja": "おしめんが最高です", "text_zh": "我的本命最棒了"},
    {"id": 2, "text_ja": "あくしゅかい楽しみ", "text_zh": "期待握手会"},
]

# 翻訳テスト用
test_segments_translation = [
    {"id": 1, "text_ja": "センターに立ちたい", "text_zh": "想站在中心"},
]

# 一貫性テスト用（用語不統一）
test_segments_consistency = [
    {"id": 1, "text_ja": "ファンの皆さん", "text_zh": "各位粉丝"},
    {"id": 2, "text_ja": "ファンの応援", "text_zh": "饭的应援"},
]
```

---

## 8. 実装順序

1. `models/suggestion.py` - Suggestionデータクラス
2. `core/checker.py` - 基底クラス・共通処理
3. `core/checker.py` - check_recognition実装
4. `core/checker.py` - check_translation実装
5. `core/checker.py` - check_consistency実装
6. `core/checker.py` - check_all統合
7. `core/pipeline.py` - パイプライン統合
8. テスト実装

---

## 9. 完了条件

- [ ] 誤認識チェックが動作する
- [ ] 翻訳チェックが動作する
- [ ] 一貫性チェックが動作する
- [ ] 提案がセグメントに紐付けられる
- [ ] ステータスが正しく更新される
- [ ] 辞書追加候補が検出される
- [ ] エラー時に適切にハンドリングされる
- [ ] 単体テストがパスする
