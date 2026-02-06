#!/usr/bin/env python3
"""
BGM管理モジュール - クラシック音楽の検索とダウンロード
"""
import os
import requests
from pathlib import Path
from typing import List, Optional


class BGMManager:
    """クラシック音楽BGMの管理"""
    
    # デフォルトのBGMリスト（ローカルライブラリ）
    DEFAULT_BGM_LIBRARY = [
        {
            "title": "Gymnopedie No. 1",
            "composer": "Kevin MacLeod (Satie style)",
            "work": "Gymnopedie No. 1",
            "mood": "穏やか、瞑想的",
            "local_file": "bgm_library/Gymnopedie_No_1.mp3",
            "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Gymnopedie%20No%201.mp3",
            "recommended_for": ["静謐な作品", "思索的な内容", "印象派"]
        },
        {
            "title": "Meditation Impromptu 02",
            "composer": "Kevin MacLeod",
            "work": "Meditation Impromptu 02",
            "mood": "静謐、神秘的",
            "local_file": "bgm_library/Meditation_Impromptu_02.mp3",
            "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Meditation%20Impromptu%2002.mp3",
            "recommended_for": ["印象派", "夜の風景", "静かな作品"]
        },
    ]
    
    def __init__(self):
        """初期化"""
        self.bgm_library = self.DEFAULT_BGM_LIBRARY.copy()
    
    def search_bgm(self, theme: str, mood: Optional[str] = None) -> List[dict]:
        """
        テーマに合ったBGMを検索
        
        Args:
            theme: エピソードのテーマ（例: "モネの睡蓮"）
            mood: 希望する雰囲気（例: "穏やか"）
        
        Returns:
            List[dict]: マッチするBGMのリスト
        """
        print(f"  🔍 BGM検索中: テーマ='{theme}', 雰囲気='{mood}'")
        
        results = []
        
        # キーワードマッチング
        theme_lower = theme.lower()
        keywords = ["モネ", "印象派", "睡蓮", "水", "光"]
        
        for bgm in self.bgm_library:
            score = 0
            
            # テーマキーワードとのマッチング
            for keyword in keywords:
                if keyword in theme:
                    for rec in bgm.get("recommended_for", []):
                        if keyword.lower() in rec.lower() or "印象派" in rec:
                            score += 1
            
            # 雰囲気のマッチング
            if mood and mood in bgm.get("mood", ""):
                score += 2
            
            if score > 0:
                bgm_copy = bgm.copy()
                bgm_copy["score"] = score
                results.append(bgm_copy)
        
        # スコア順にソート
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # マッチしなければ最初のBGMを返す
        if not results:
            results = [self.bgm_library[0].copy()]
        
        print(f"  ✅ {len(results)}件のBGM候補を発見")
        
        return results
    
    def download_bgm(self, bgm_info: dict, output_dir: Path) -> Optional[Path]:
        """
        BGMをダウンロード（またはローカルからコピー）
        
        Args:
            bgm_info: BGM情報辞書
            output_dir: 出力ディレクトリ
        
        Returns:
            Optional[Path]: ダウンロードされたファイルのパス（失敗時はNone）
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        title = bgm_info.get("title", "unknown")
        
        # ローカルファイルがあればコピー
        local_file = bgm_info.get("local_file")
        if local_file:
            local_path = Path(__file__).parent.parent / local_file
            if local_path.exists():
                # ファイル名を生成
                output_path = output_dir / local_path.name
                
                # 既にコピー済みならスキップ
                if output_path.exists():
                    print(f"  ✓ 既にコピー済み: {output_path.name}")
                    return output_path
                
                # ローカルファイルをコピー
                print(f"  📋 ローカルBGMをコピー: {title}")
                import shutil
                shutil.copy2(local_path, output_path)
                
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ コピー完了: {file_size_mb:.1f} MB")
                
                return output_path
        
        # ローカルになければダウンロード
        url = bgm_info.get("url")
        if not url:
            print(f"  ⚠️ BGM URLが見つかりません: {title}")
            return None
        
        # ファイル名を生成
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        # 拡張子を取得（URLから）
        ext = Path(url).suffix or ".mp3"
        output_path = output_dir / f"{safe_title}{ext}"
        
        # 既にダウンロード済みならスキップ
        if output_path.exists():
            print(f"  ✓ 既にダウンロード済み: {output_path.name}")
            return output_path
        
        print(f"  📥 ダウンロード中: {title}")
        print(f"     URL: {url}")
        
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ ダウンロード完了: {file_size_mb:.1f} MB")
            
            return output_path
            
        except requests.RequestException as e:
            print(f"  ❌ ダウンロード失敗: {e}")
            return None
    
    def get_bgm_for_episode(self, theme: str, output_dir: Path, mood: Optional[str] = None) -> Optional[Path]:
        """
        エピソード用のBGMを取得（検索＋ダウンロード）
        
        Args:
            theme: エピソードのテーマ
            output_dir: 出力ディレクトリ
            mood: 希望する雰囲気
        
        Returns:
            Optional[Path]: BGMファイルのパス
        """
        # BGM検索
        bgm_candidates = self.search_bgm(theme, mood)
        
        if not bgm_candidates:
            print("  ⚠️ 適切なBGMが見つかりませんでした")
            return None
        
        # 最もスコアの高いBGMを使用
        best_bgm = bgm_candidates[0]
        print(f"  🎵 選択されたBGM: {best_bgm['title']}")
        print(f"     作曲家: {best_bgm['composer']}")
        print(f"     雰囲気: {best_bgm['mood']}")
        
        # ダウンロード
        bgm_path = self.download_bgm(best_bgm, output_dir)
        
        return bgm_path
    
    def add_bgm(self, bgm_info: dict):
        """
        BGMライブラリに新しいBGMを追加
        
        Args:
            bgm_info: BGM情報辞書
        """
        self.bgm_library.append(bgm_info)
        print(f"  ✅ BGMを追加: {bgm_info.get('title', 'Unknown')}")


if __name__ == "__main__":
    # テスト
    import tempfile
    
    print("🎵 BGMManager テスト\n")
    
    manager = BGMManager()
    
    print("--- BGM検索テスト ---")
    results = manager.search_bgm("モネの睡蓮", mood="穏やか")
    for i, bgm in enumerate(results[:3], 1):
        print(f"{i}. {bgm['title']} (スコア: {bgm.get('score', 0)})")
    
    print("\n--- BGMダウンロードテスト ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "bgm"
        bgm_path = manager.get_bgm_for_episode("モネの睡蓮", output_dir)
        
        if bgm_path:
            print(f"\n✅ テスト成功: {bgm_path}")
        else:
            print("\n⚠️ ダウンロードをスキップ（テスト環境）")
