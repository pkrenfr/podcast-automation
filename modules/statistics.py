#!/usr/bin/env python3
"""
統計管理モジュール
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class StatisticsManager:
    """ポッドキャスト統計の記録と管理"""
    
    def __init__(self, stats_file: Path = None):
        """
        初期化
        
        Args:
            stats_file: 統計ファイルのパス（デフォルト: statistics.json）
        """
        if stats_file is None:
            stats_file = Path(__file__).parent.parent / "statistics.json"
        
        self.stats_file = stats_file
        self.data = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """統計ファイルを読み込み"""
        if not self.stats_file.exists():
            return {
                "episodes": [],
                "summary": {
                    "total_episodes": 0,
                    "average_characters_per_second": 0,
                    "average_dialogue_characters_per_second": 0,
                    "prediction_formula": "duration_seconds = dialogue_characters / avg_cps"
                },
                "recommendations": {}
            }
        
        with open(self.stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_stats(self):
        """統計ファイルに保存"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_episode(
        self,
        theme: str,
        folder: str,
        script_path: Path,
        audio_path: Path,
        segments: int,
        duration_seconds: float,
        voice_settings: Dict = None
    ):
        """
        新しいエピソードの統計を追加
        
        Args:
            theme: エピソードのテーマ
            folder: 出力フォルダ名
            script_path: 台本ファイルのパス
            audio_path: 音声ファイルのパス
            segments: セグメント数
            duration_seconds: 音声の長さ（秒）
            voice_settings: 音声設定
        """
        # 台本の文字数をカウント
        total_chars, dialogue_chars, speaker_counts = self._count_script_characters(script_path)
        
        # ファイルサイズ取得
        mp3_size_mb = 0
        wav_size_mb = 0
        
        if audio_path.suffix == '.mp3':
            mp3_size_mb = audio_path.stat().st_size / (1024 * 1024)
            wav_path = audio_path.with_suffix('.wav')
            if wav_path.exists():
                wav_size_mb = wav_path.stat().st_size / (1024 * 1024)
        else:
            wav_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        # 文字/秒を計算
        chars_per_sec = dialogue_chars / duration_seconds if duration_seconds > 0 else 0
        
        # エピソードデータ作成
        episode_data = {
            "episode_id": len(self.data["episodes"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "theme": theme,
            "folder": folder,
            "stats": {
                "total_characters": total_chars,
                "dialogue_characters": dialogue_chars,
                "segments": segments,
                "duration_seconds": round(duration_seconds, 1),
                "characters_per_second": round(chars_per_sec, 2),
                "mp3_file_size_mb": round(mp3_size_mb, 1),
                "wav_file_size_mb": round(wav_size_mb, 1)
            },
            "voice_settings": voice_settings or {
                "speed_scale": 1.0,
                "pitch_scale": 0.0,
                "intonation_scale": 1.0
            },
            "speakers": speaker_counts
        }
        
        # データに追加
        self.data["episodes"].append(episode_data)
        
        # サマリー更新
        self._update_summary()
        
        # 保存
        self._save_stats()
        
        print(f"\n📊 統計を更新しました:")
        print(f"   エピソード #{episode_data['episode_id']}")
        print(f"   台詞文字数: {dialogue_chars}文字")
        print(f"   音声長: {duration_seconds:.1f}秒")
        print(f"   文字/秒: {chars_per_sec:.2f}")
        
        return episode_data
    
    def _count_script_characters(self, script_path: Path) -> tuple:
        """
        台本の文字数をカウント
        
        Returns:
            (総文字数, 台詞文字数, 話者別カウント)
        """
        if not script_path.exists():
            return (0, 0, {})
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        total_chars = len(content)
        dialogue_chars = 0
        speaker_counts = {"zundamon": 0, "metan": 0}
        
        # 台詞行を抽出
        for line in content.split('\n'):
            if line.startswith('**'):
                # 話者名を除去
                if ':' in line:
                    _, text = line.split(':', 1)
                    text = text.strip()
                    dialogue_chars += len(text)
                    
                    # 話者カウント
                    if 'ずんだもん' in line:
                        speaker_counts['zundamon'] += 1
                    elif 'めたん' in line:
                        speaker_counts['metan'] += 1
        
        return (total_chars, dialogue_chars, speaker_counts)
    
    def _update_summary(self):
        """サマリーを更新"""
        episodes = self.data["episodes"]
        
        if not episodes:
            return
        
        total_episodes = len(episodes)
        
        # 平均文字/秒を計算
        total_cps = sum(ep["stats"]["characters_per_second"] for ep in episodes)
        avg_cps = total_cps / total_episodes
        
        # 平均台詞文字/秒を計算
        total_dialogue_cps = sum(
            ep["stats"]["dialogue_characters"] / ep["stats"]["duration_seconds"]
            for ep in episodes
            if ep["stats"]["duration_seconds"] > 0
        )
        avg_dialogue_cps = total_dialogue_cps / total_episodes
        
        self.data["summary"] = {
            "total_episodes": total_episodes,
            "average_characters_per_second": round(avg_cps, 2),
            "average_dialogue_characters_per_second": round(avg_dialogue_cps, 2),
            "prediction_formula": f"duration_seconds = dialogue_characters / {avg_dialogue_cps:.2f}"
        }
        
        # 推奨文字数を更新
        self.data["recommendations"] = {
            "3_minutes": {
                "target_seconds": 180,
                "recommended_characters": int(180 * avg_dialogue_cps)
            },
            "5_minutes": {
                "target_seconds": 300,
                "recommended_characters": int(300 * avg_dialogue_cps)
            },
            "8_minutes": {
                "target_seconds": 480,
                "recommended_characters": int(480 * avg_dialogue_cps)
            },
            "10_minutes": {
                "target_seconds": 600,
                "recommended_characters": int(600 * avg_dialogue_cps)
            },
            "15_minutes": {
                "target_seconds": 900,
                "recommended_characters": int(900 * avg_dialogue_cps)
            }
        }
    
    def get_recommended_characters(self, target_minutes: float) -> int:
        """
        目標時間から推奨文字数を取得
        
        Args:
            target_minutes: 目標時間（分）
        
        Returns:
            int: 推奨台詞文字数
        """
        if not self.data["episodes"]:
            # デフォルト値（13.7文字/秒）
            return int(target_minutes * 60 * 13.7)
        
        avg_cps = self.data["summary"]["average_dialogue_characters_per_second"]
        return int(target_minutes * 60 * avg_cps)
    
    def print_summary(self):
        """統計サマリーを表示"""
        summary = self.data["summary"]
        
        print("\n📊 統計サマリー")
        print(f"   総エピソード数: {summary['total_episodes']}")
        print(f"   平均文字/秒: {summary['average_dialogue_characters_per_second']:.2f}")
        print(f"   予測式: {summary['prediction_formula']}")
        
        print("\n🎯 推奨文字数:")
        for key, rec in self.data["recommendations"].items():
            minutes = rec["target_seconds"] / 60
            print(f"   {minutes:.0f}分 → {rec['recommended_characters']:,}文字")


if __name__ == "__main__":
    # テスト
    stats = StatisticsManager()
    stats.print_summary()
