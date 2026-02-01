# Phase 4: 辞書管理機能 - 要件定義書

## 1. 概要

### 1.1 目的
カスタム辞書のCRUD機能、学習候補管理、パイプラインへの統合を実装する。

### 1.2 スコープ
- 辞書データのCRUD操作
- 辞書のインポート/エクスポート
- 学習候補（チェックAgentが検出した新語）の管理
- パイプラインへの辞書適用統合
- 辞書適用の統計・ログ

### 1.3 前提条件
- Phase 1〜3が完了していること
- 辞書データの保存先（JSON）が確保されていること

### 1.4 成果物
- 辞書管理モジュール
- パイプラインへの辞書適用機能
- 学習候補管理機能

---

## 2. データ設計

### 2.1 辞書エントリ（DictionaryEntry）

```python
@dataclass
class DictionaryEntry:
    id: int                   # 一意のID
    wrong: str                # 誤認識パターン（検索対象）
    correct: str              # 正しい表記（置換先）
    category: str             # カテゴリ
    created_at: datetime      # 作成日時
    updated_at: datetime      # 更新日時
    used_count: int           # 使用回数（適用された回数）
    is_regex: bool            # 正規表現フラグ（将来拡張用）
    is_enabled: bool          # 有効/無効フラグ
    notes: str                # 備考（オプション）
```

### 2.2 学習候補（PendingSuggestion）

```python
@dataclass
class PendingSuggestion:
    id: int                   # 一意のID
    wrong: str                # 誤認識パターン
    correct: str              # 提案される正しい表記
    category: str             # 推定カテゴリ
    occurrences: int          # 検出回数
    confidence: float         # 信頼度（0.0-1.0）
    first_detected: datetime  # 初回検出日時
    last_detected: datetime   # 最終検出日時
    source_segments: List[int] # 検出元セグメントID
```

### 2.3 辞書ファイル形式（JSON）

```json
{
  "version": "1.0",
  "updated_at": "2024-01-15T10:30:00Z",
  "entries": [
    {
      "id": 1,
      "wrong": "おしめん",
      "correct": "推しメン",
      "category": "アイドル用語",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "used_count": 15,
      "is_regex": false,
      "is_enabled": true,
      "notes": ""
    }
  ],
  "pending_suggestions": [
    {
      "id": 1,
      "wrong": "えーけーびー",
      "correct": "AKB",
      "category": "グループ名",
      "occurrences": 5,
      "confidence": 0.92,
      "first_detected": "2024-01-10T00:00:00Z",
      "last_detected": "2024-01-15T00:00:00Z",
      "source_segments": [12, 45, 78, 102, 134]
    }
  ],
  "categories": [
    "アイドル用語",
    "メンバー名",
    "グループ名",
    "楽曲名",
    "その他"
  ],
  "statistics": {
    "total_entries": 24,
    "total_applications": 156,
    "most_used": [
      {"wrong": "おしめん", "count": 15},
      {"wrong": "あくしゅかい", "count": 12}
    ]
  }
}
```

---

## 3. 機能詳細

### 3.1 辞書管理モジュール（dictionary.py）

#### 3.1.1 クラス設計

```python
class DictionaryManager:
    def __init__(self, dictionary_path: str = "data/dictionary.json"):
        self.dictionary_path = dictionary_path
        self.entries: List[DictionaryEntry] = []
        self.pending: List[PendingSuggestion] = []
        self.categories: List[str] = []
        self._load()
    
    # CRUD操作
    def add_entry(self, entry: DictionaryEntry) -> int
    def get_entry(self, entry_id: int) -> DictionaryEntry | None
    def update_entry(self, entry_id: int, updates: dict) -> bool
    def delete_entry(self, entry_id: int) -> bool
    
    # 検索・フィルタ
    def search(self, query: str) -> List[DictionaryEntry]
    def filter_by_category(self, category: str) -> List[DictionaryEntry]
    def get_all_entries(self) -> List[DictionaryEntry]
    
    # 学習候補管理
    def add_pending(self, suggestion: PendingSuggestion) -> int
    def accept_pending(self, pending_id: int) -> DictionaryEntry
    def reject_pending(self, pending_id: int) -> bool
    def get_all_pending(self) -> List[PendingSuggestion]
    
    # インポート/エクスポート
    def import_from_json(self, file_path: str) -> int
    def export_to_json(self, file_path: str) -> str
    def import_from_csv(self, file_path: str) -> int
    def export_to_csv(self, file_path: str) -> str
    
    # カテゴリ管理
    def add_category(self, category: str) -> bool
    def get_categories(self) -> List[str]
    
    # 統計
    def get_statistics(self) -> dict
    
    # 内部メソッド
    def _load(self) -> None
    def _save(self) -> None
    def _generate_id(self) -> int
```

#### 3.1.2 CRUD操作の仕様

```python
def add_entry(self, entry: DictionaryEntry) -> int:
    """
    辞書エントリを追加する
    
    Args:
        entry: 追加するエントリ（idは自動生成）
    
    Returns:
        生成されたID
    
    処理:
        1. IDを自動生成
        2. created_at, updated_atを設定
        3. entriesに追加
        4. 保存
        5. IDを返す
    
    例外:
        ValueError: wrongが空の場合
        ValueError: 同じwrongが既に存在する場合
    """

def update_entry(self, entry_id: int, updates: dict) -> bool:
    """
    辞書エントリを更新する
    
    Args:
        entry_id: 更新対象のID
        updates: 更新するフィールドと値の辞書
    
    Returns:
        成功した場合True
    
    更新可能フィールド:
        - wrong
        - correct
        - category
        - is_enabled
        - notes
    
    処理:
        1. IDでエントリを検索
        2. updatesの各フィールドを更新
        3. updated_atを更新
        4. 保存
    """

def delete_entry(self, entry_id: int) -> bool:
    """
    辞書エントリを削除する
    
    Args:
        entry_id: 削除対象のID
    
    Returns:
        成功した場合True
    
    処理:
        1. IDでエントリを検索
        2. entriesから削除
        3. 保存
    """
```

#### 3.1.3 検索・フィルタの仕様

```python
def search(self, query: str) -> List[DictionaryEntry]:
    """
    辞書を検索する
    
    Args:
        query: 検索クエリ
    
    Returns:
        マッチしたエントリのリスト
    
    検索対象:
        - wrong（部分一致）
        - correct（部分一致）
        - notes（部分一致）
    """

def filter_by_category(self, category: str) -> List[DictionaryEntry]:
    """
    カテゴリでフィルタする
    
    Args:
        category: カテゴリ名
    
    Returns:
        該当カテゴリのエントリリスト
    """
```

---

### 3.2 辞書適用モジュール（text_processor.py）

#### 3.2.1 機能説明

音声認識結果に対して辞書を適用し、既知の誤認識パターンを置換する。

#### 3.2.2 処理仕様

```python
class TextProcessor:
    def __init__(self, dictionary_manager: DictionaryManager):
        self.dictionary = dictionary_manager
        self.application_log: List[dict] = []
    
    def apply_dictionary(self, text: str) -> Tuple[str, List[dict]]:
        """
        テキストに辞書を適用する
        
        Args:
            text: 入力テキスト
        
        Returns:
            (変換後テキスト, 適用ログ)
        
        処理:
            1. 有効なエントリを取得
            2. 各エントリについてテキスト内を検索
            3. マッチした場合は置換
            4. 適用ログを記録
            5. used_countを更新
        """
    
    def apply_to_segments(
        self,
        segments: List[Segment]
    ) -> Tuple[List[Segment], dict]:
        """
        セグメントリストに辞書を適用する
        
        Args:
            segments: 入力セグメント
        
        Returns:
            (変換後セグメント, 統計情報)
        
        統計情報:
            {
                "total_replacements": 12,
                "entries_used": ["おしめん", "あくしゅかい", ...],
                "segments_modified": [1, 5, 12, ...]
            }
        """
    
    def get_application_log(self) -> List[dict]:
        """適用ログを取得"""
        return self.application_log
```

#### 3.2.3 適用ログ形式

```python
application_log = [
    {
        "segment_id": 12,
        "entry_id": 1,
        "wrong": "おしめん",
        "correct": "推しメン",
        "original_text": "おしめんが最高です",
        "modified_text": "推しメンが最高です",
        "timestamp": "2024-01-15T10:30:00Z"
    }
]
```

---

### 3.3 学習候補管理

#### 3.3.1 候補の登録

```python
def register_pending_from_checker(
    self,
    suggestions: List[Suggestion]
) -> int:
    """
    チェックAgentの結果から学習候補を登録する
    
    Args:
        suggestions: チェック結果の提案リスト
    
    Returns:
        登録された候補数
    
    処理:
        1. add_to_dict=Trueの提案を抽出
        2. 既存の候補と重複チェック
        3. 重複の場合はoccurrencesを加算
        4. 新規の場合は候補として追加
    """
```

#### 3.3.2 候補の承認

```python
def accept_pending(self, pending_id: int) -> DictionaryEntry:
    """
    学習候補を承認して辞書に追加する
    
    Args:
        pending_id: 候補ID
    
    Returns:
        追加されたエントリ
    
    処理:
        1. 候補を取得
        2. DictionaryEntryに変換
        3. 辞書に追加
        4. 候補から削除
        5. 保存
    """
```

#### 3.3.3 候補の却下

```python
def reject_pending(self, pending_id: int) -> bool:
    """
    学習候補を却下する
    
    Args:
        pending_id: 候補ID
    
    Returns:
        成功した場合True
    
    処理:
        1. 候補を取得
        2. 候補から削除
        3. 保存
    """
```

---

### 3.4 インポート/エクスポート

#### 3.4.1 JSONインポート

```python
def import_from_json(self, file_path: str) -> int:
    """
    JSONファイルから辞書をインポートする
    
    Args:
        file_path: インポートファイルパス
    
    Returns:
        インポートされたエントリ数
    
    処理:
        1. JSONファイルを読み込み
        2. バリデーション
        3. 重複チェック（wrongで判定）
        4. 重複の場合はスキップまたは更新
        5. 新規エントリを追加
        6. 保存
    
    対応形式:
        - 本ツールのエクスポート形式
        - シンプル形式: [{"wrong": "...", "correct": "..."}]
    """
```

#### 3.4.2 CSVインポート

```python
def import_from_csv(self, file_path: str) -> int:
    """
    CSVファイルから辞書をインポートする
    
    Args:
        file_path: インポートファイルパス
    
    Returns:
        インポートされたエントリ数
    
    CSV形式:
        wrong,correct,category
        おしめん,推しメン,アイドル用語
        あくしゅかい,握手会,アイドル用語
    """
```

#### 3.4.3 エクスポート

```python
def export_to_json(self, file_path: str) -> str:
    """
    辞書をJSONファイルにエクスポートする
    
    Args:
        file_path: 出力ファイルパス
    
    Returns:
        出力ファイルパス
    """

def export_to_csv(self, file_path: str) -> str:
    """
    辞書をCSVファイルにエクスポートする
    
    Args:
        file_path: 出力ファイルパス
    
    Returns:
        出力ファイルパス
    """
```

---

## 4. パイプライン統合

### 4.1 更新後のフロー

```
video.mp4
    │
    ▼
[音声抽出]
    │
    ▼
[話者識別] + [文字起こし]
    │
    ▼
[マージ]
    │
    ▼
┌─────────────────────────┐
│  辞書適用（Phase 4新規） │
│                         │
│  ・既知パターンを置換   │
│  ・適用ログを記録       │
│  ・統計を更新           │
└─────────────────────────┘
    │
    ▼
[翻訳]
    │
    ▼
[品質チェック]
    │
    ▼
┌─────────────────────────┐
│ 学習候補登録（Phase 4）  │
│                         │
│  ・新規パターンを候補化 │
└─────────────────────────┘
    │
    ▼
[レビュー]
    │
    ▼
[ASS出力]
```

### 4.2 パイプラインコード

```python
def process_video(video_path: str, config: Config) -> ProcessResult:
    """更新後のパイプライン"""
    
    # 前処理
    audio_path = extract_audio(video_path)
    diarization = diarize(audio_path)
    transcription = transcribe(audio_path, config.initial_prompt)
    segments = merge_segments(transcription, diarization)
    
    # Phase 4: 辞書適用
    dictionary = DictionaryManager(config.dictionary_path)
    processor = TextProcessor(dictionary)
    segments, dict_stats = processor.apply_to_segments(segments)
    
    # 翻訳
    segments = translate_segments(segments, config.claude_api_key)
    
    # 品質チェック
    checker = SubtitleChecker(config.claude_api_key)
    segments, suggestions = checker.check_all(segments)
    
    # Phase 4: 学習候補登録
    new_candidates = dictionary.register_pending_from_checker(suggestions)
    
    # ASS出力
    ass_path = generate_ass(segments, config.output_dir)
    
    return ProcessResult(
        segments=segments,
        suggestions=suggestions,
        ass_path=ass_path,
        stats={
            "dictionary": dict_stats,
            "new_candidates": new_candidates
        }
    )
```

---

## 5. 統計機能

### 5.1 統計データ

```python
def get_statistics(self) -> dict:
    """
    辞書の統計情報を取得する
    
    Returns:
        {
            "total_entries": 24,
            "enabled_entries": 22,
            "disabled_entries": 2,
            "categories": {
                "アイドル用語": 15,
                "メンバー名": 5,
                "グループ名": 3,
                "その他": 1
            },
            "total_applications": 156,
            "most_used": [
                {"wrong": "おしめん", "correct": "推しメン", "count": 25},
                {"wrong": "あくしゅかい", "correct": "握手会", "count": 18}
            ],
            "least_used": [
                {"wrong": "...", "correct": "...", "count": 0}
            ],
            "pending_count": 3,
            "recent_additions": [...]
        }
    """
```

### 5.2 使用回数の更新

```python
def increment_used_count(self, entry_id: int) -> None:
    """
    使用回数をインクリメントする
    
    処理:
        1. エントリを取得
        2. used_countを+1
        3. 保存
    """
```

---

## 6. エラーハンドリング

### 6.1 例外クラス

```python
class DictionaryError(Exception):
    """辞書関連の基底例外"""
    pass

class DuplicateEntryError(DictionaryError):
    """重複エントリエラー"""
    pass

class EntryNotFoundError(DictionaryError):
    """エントリ未検出エラー"""
    pass

class ImportError(DictionaryError):
    """インポートエラー"""
    pass

class ExportError(DictionaryError):
    """エクスポートエラー"""
    pass
```

### 6.2 エラー処理

| エラー | 対処 |
|--------|------|
| 重複エントリ | 警告を出して既存を優先、またはユーザーに選択させる |
| エントリ未検出 | EntryNotFoundErrorを発生 |
| ファイル読み込み失敗 | ImportErrorを発生、詳細をログ |
| バリデーション失敗 | ValueErrorを発生、不正な項目を明示 |

---

## 7. バリデーション

### 7.1 エントリのバリデーション

```python
def validate_entry(entry: DictionaryEntry) -> List[str]:
    """
    エントリをバリデーションする
    
    Returns:
        エラーメッセージのリスト（空ならOK）
    
    チェック項目:
        - wrongが空でない
        - correctが空でない
        - wrongとcorrectが同じでない
        - カテゴリが有効
    """
    errors = []
    
    if not entry.wrong or not entry.wrong.strip():
        errors.append("誤認識パターンは必須です")
    
    if not entry.correct or not entry.correct.strip():
        errors.append("正しい表記は必須です")
    
    if entry.wrong == entry.correct:
        errors.append("誤認識パターンと正しい表記が同じです")
    
    return errors
```

---

## 8. ファイル構成

```
models/
├── __init__.py
├── segment.py           # セグメント（既存）
├── suggestion.py        # 提案（既存）
└── dictionary.py        # 辞書エントリ、学習候補

core/
├── __init__.py
├── ...（既存モジュール）
└── text_processor.py    # テキスト処理、辞書適用

utils/
├── __init__.py
├── ...（既存ユーティリティ）
└── dictionary_manager.py # 辞書管理

data/
├── dictionary.json      # メイン辞書ファイル
└── dictionary_backup/   # バックアップ
```

---

## 9. テスト要件

### 9.1 単体テスト

| テスト対象 | テスト内容 |
|-----------|-----------|
| add_entry | エントリが正しく追加されるか |
| update_entry | エントリが正しく更新されるか |
| delete_entry | エントリが正しく削除されるか |
| search | 検索結果が正しいか |
| apply_dictionary | テキストが正しく置換されるか |
| import_from_json | JSONが正しくインポートされるか |
| export_to_json | JSONが正しくエクスポートされるか |
| accept_pending | 候補が正しく辞書に追加されるか |

### 9.2 統合テスト

| テスト項目 | 内容 |
|-----------|------|
| パイプライン統合 | 辞書適用がパイプラインで動作するか |
| 学習候補フロー | チェック→候補登録→承認の流れ |
| UI連携 | WebUIから辞書操作が正しく動作するか |

### 9.3 テストデータ

```python
# テスト用辞書
test_dictionary = {
    "entries": [
        {"wrong": "おしめん", "correct": "推しメン", "category": "アイドル用語"},
        {"wrong": "あくしゅかい", "correct": "握手会", "category": "アイドル用語"},
    ]
}

# テスト用テキスト
test_text = "おしめんが最高です。あくしゅかい楽しみ。"
expected_text = "推しメンが最高です。握手会楽しみ。"
```

---

## 10. 実装順序

1. `models/dictionary.py` - DictionaryEntry, PendingSuggestionデータクラス
2. `utils/dictionary_manager.py` - DictionaryManager基本実装
3. `utils/dictionary_manager.py` - CRUD操作
4. `utils/dictionary_manager.py` - 検索・フィルタ
5. `utils/dictionary_manager.py` - インポート/エクスポート
6. `utils/dictionary_manager.py` - 学習候補管理
7. `core/text_processor.py` - 辞書適用
8. `core/pipeline.py` - パイプライン統合
9. `ui/dictionary_tab.py` - WebUI連携強化
10. テスト実装

---

## 11. 完了条件

- [ ] 辞書のCRUD操作が動作する
- [ ] 検索・フィルタが動作する
- [ ] JSONインポート/エクスポートが動作する
- [ ] CSVインポート/エクスポートが動作する
- [ ] 辞書適用がパイプラインで動作する
- [ ] 適用ログが記録される
- [ ] 使用回数がカウントされる
- [ ] 学習候補の登録が動作する
- [ ] 学習候補の承認/却下が動作する
- [ ] 統計情報が取得できる
- [ ] WebUIから全機能が操作できる
- [ ] 単体テストがパスする

---

## 12. 将来の拡張案

### 12.1 正規表現対応

```python
# is_regex=Trueの場合
entry = DictionaryEntry(
    wrong=r"[0-9]+期生",
    correct=lambda m: f"{m.group()}",  # そのまま
    is_regex=True
)
```

### 12.2 コンテキスト依存置換

```python
# 前後の文脈を考慮した置換
entry = DictionaryEntry(
    wrong="センター",
    correct="C位",
    context="中国語翻訳時のみ"
)
```

### 12.3 辞書の共有・同期

- クラウド同期機能
- 複数ユーザー間での辞書共有
- バージョン管理
