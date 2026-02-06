#!/usr/bin/env python3
"""
ポッドキャスト自動生成メインスクリプト
"""
import os
import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# リソース監視
from modules.resource_monitor import ResourceMonitor, set_low_priority

class PodcastGenerator:
    def __init__(self, config_path="config.yaml", enable_monitoring=True):
        """初期化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.output_base = Path(self.config['output']['base_dir'])
        self.output_base.mkdir(exist_ok=True)
        
        # リソースモニタリング
        self.monitor = ResourceMonitor() if enable_monitoring else None
        
        # プロセス優先度を下げる（他への影響軽減）
        if enable_monitoring:
            set_low_priority()
    
    def create_episode_dir(self, episode_name):
        """エピソードディレクトリ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        episode_dir = self.output_base / f"{timestamp}_{episode_name}"
        episode_dir.mkdir(exist_ok=True)
        
        # サブディレクトリ作成
        (episode_dir / "voice_segments").mkdir(exist_ok=True)
        (episode_dir / "bgm").mkdir(exist_ok=True)
        
        return episode_dir
    
    def generate(self, theme, episode_name=None):
        """ポッドキャスト生成メイン処理"""
        print(f"🎨 テーマ: {theme}")
        
        if episode_name is None:
            episode_name = theme.replace(" ", "_").replace("/", "_")
        
        episode_dir = self.create_episode_dir(episode_name)
        print(f"📁 出力先: {episode_dir}")
        
        # Step 1: 原稿生成
        print("\n📝 Step 1: 原稿生成中...")
        script = self.generate_script(theme, episode_dir)
        
        # Step 2: 音声合成
        print("\n🎤 Step 2: 音声合成中...")
        voice_files = self.synthesize_voices(script, episode_dir)
        
        # Step 3: BGM準備
        print("\n🎵 Step 3: BGM準備中...")
        bgm_file = self.prepare_bgm(theme, episode_dir)
        
        # Step 4: 音声ミックス
        print("\n🎛️ Step 4: 音声ミックス中...")
        mixed_audio = self.mix_audio(voice_files, bgm_file, episode_dir)
        
        # Step 5: Audacityプロジェクト生成
        print("\n💾 Step 5: Audacityプロジェクト保存中...")
        project_file = self.create_audacity_project(voice_files, bgm_file, episode_dir)
        
        # Step 6: 統計を記録
        print("\n📊 Step 6: 統計記録中...")
        self._record_statistics(theme, episode_dir, script, voice_files, mixed_audio)
        
        print(f"\n✅ 完了！")
        print(f"📂 プロジェクトファイル: {project_file}")
        print(f"🎧 ミックス音声: {mixed_audio}")
        print(f"\nAudacityで開いてレビュー後、最終エクスポートしてください。")
        
        return episode_dir
    
    def generate_script(self, theme, episode_dir):
        """原稿生成"""
        from modules.researcher import PodcastResearcher
        
        researcher = PodcastResearcher()
        
        # テーマをリサーチ
        research_data = researcher.research_topic(theme)
        
        # 台本を生成
        script = researcher.generate_script(theme, research_data, episode_length="medium")
        
        # 台本を保存
        script_path = episode_dir / "script.md"
        researcher.save_script(script, script_path)
        
        print(f"  ✅ 原稿保存: {script_path}")
        return script
    
    def synthesize_voices(self, script, episode_dir):
        """音声合成"""
        from modules.voicevox import VoicevoxClient
        
        print("  ⏳ VOICEVOX APIに接続中...")
        
        # リソースチェック
        if self.monitor:
            self.monitor.check(verbose=True)
            self.monitor.wait_if_busy(max_wait_sec=30)
        
        voicevox = VoicevoxClient(self.config['voice']['voicevox_url'])
        
        if not voicevox.is_available():
            print("  ❌ VOICEVOXが起動していません")
            print("  起動: docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest")
            raise RuntimeError("VOICEVOX not available")
        
        segments_dir = episode_dir / "voice_segments"
        
        # チャンクサイズを設定から取得（デフォルト: 10）
        chunk_size = self.config.get('processing', {}).get('chunk_size', 10)
        cooldown = self.config.get('processing', {}).get('cooldown_sec', 0.5)
        
        voice_files = voicevox.synthesize_segments(
            script['segments'],
            segments_dir,
            speed_scale=self.config['voice'].get('speed_scale', 1.0),
            pitch_scale=self.config['voice'].get('pitch_scale', 0.0),
            intonation_scale=self.config['voice'].get('intonation_scale', 1.0),
            chunk_size=chunk_size,
            cooldown_sec=cooldown
        )
        
        # 完了後のリソースチェック
        if self.monitor:
            print()
            self.monitor.check(verbose=True)
        
        print(f"  ✅ {len(voice_files)}個の音声セグメント生成完了")
        return voice_files
    
    def prepare_bgm(self, theme, episode_dir):
        """BGM準備"""
        from modules.bgm_manager import BGMManager
        
        manager = BGMManager()
        bgm_dir = episode_dir / "bgm"
        
        bgm_file = manager.get_bgm_for_episode(theme, bgm_dir, mood="穏やか")
        
        if bgm_file is None or not bgm_file.exists():
            print(f"  ⚠️ BGMダウンロード失敗。無音を使用します")
            # ダミーBGMファイル作成（1秒の無音）
            bgm_file = bgm_dir / "silent.mp3"
            bgm_dir.mkdir(exist_ok=True, parents=True)
            # TODO: 実際には無音MP3を生成
        
        print(f"  ✅ BGM準備完了: {bgm_file}")
        return bgm_file
    
    def mix_audio(self, voice_files, bgm_file, episode_dir):
        """音声ミックス"""
        from modules.audio_mixer import AudioMixer
        
        mixer = AudioMixer(self.config)
        
        mixed_file = episode_dir / "mixed_audio.wav"
        mixer.mix(voice_files, bgm_file, mixed_file)
        
        # MP3も生成
        mp3_file = episode_dir / "mixed_audio.mp3"
        mixer.export_mp3(
            mixed_file,
            mp3_file,
            bitrate=self.config['audio'].get('export_bitrate', '192k')
        )
        
        return mixed_file
    
    def create_audacity_project(self, voice_files, bgm_file, episode_dir):
        """Audacityプロジェクト作成 - TODO: 実装"""
        project_file = episode_dir / "project.aup3"
        
        # TODO: Audacityプロジェクトファイル生成
        # または、Audacityのmod-script-pipeを使用
        
        print(f"  ✅ プロジェクト保存: {project_file}")
        return project_file
    
    def _record_statistics(self, theme, episode_dir, script, voice_files, audio_path):
        """統計を記録"""
        from modules.statistics import StatisticsManager
        from pydub import AudioSegment
        
        # 音声の長さを取得
        audio = AudioSegment.from_file(str(audio_path))
        duration_seconds = len(audio) / 1000.0
        
        # 統計マネージャー
        stats = StatisticsManager()
        
        # 台本パス
        script_path = episode_dir / "script.md"
        
        # 統計記録
        stats.add_episode(
            theme=theme,
            folder=episode_dir.name,
            script_path=script_path,
            audio_path=audio_path,
            segments=len(voice_files),
            duration_seconds=duration_seconds,
            voice_settings=self.config.get('voice', {})
        )
        
        # サマリー表示
        stats.print_summary()


def main():
    parser = argparse.ArgumentParser(description='ポッドキャスト自動生成')
    parser.add_argument('theme', help='エピソードのテーマ（例: モネの睡蓮）')
    parser.add_argument('--episode-name', help='エピソード名（省略時はテーマから生成）')
    parser.add_argument('--config', default='config.yaml', help='設定ファイル')
    parser.add_argument('--script-json', help='事前生成された台本JSONファイル', default=None)
    
    args = parser.parse_args()
    
    generator = PodcastGenerator(args.config)
    
    # 台本JSONが指定されている場合は直接読み込む
    if args.script_json:
        import json
        with open(args.script_json, 'r', encoding='utf-8') as f:
            script = json.load(f)
        print(f"✅ 台本を読み込み: {args.script_json}")
        
        # エピソード生成（台本スキップ）
        episode_name = args.episode_name or args.theme.replace(" ", "_").replace("/", "_")
        episode_dir = generator.create_episode_dir(episode_name)
        
        # 台本を保存
        script_path = episode_dir / "script.md"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"# {script['title']}\n\n> {script['description']}\n\n---\n\n")
            for seg in script['segments']:
                speaker_name = "ずんだもん" if seg['speaker'] == 'zundamon' else "四国めたん"
                f.write(f"**{speaker_name}**: {seg['text']}\n\n")
        
        # 音声合成以降の処理
        print("\n🎤 音声合成中...")
        voice_files = generator.synthesize_voices(script, episode_dir)
        
        print("\n🎵 BGM準備中...")
        bgm_file = generator.prepare_bgm(args.theme, episode_dir)
        
        print("\n🎛️ 音声ミックス中...")
        mixed_audio = generator.mix_audio(voice_files, bgm_file, episode_dir)
        
        print("\n💾 Audacityプロジェクト保存中...")
        project_file = generator.create_audacity_project(voice_files, bgm_file, episode_dir)
        
        print("\n📊 統計記録中...")
        generator._record_statistics(args.theme, episode_dir, script, voice_files, mixed_audio)
        
        print(f"\n✅ 完了！")
        print(f"📂 プロジェクトファイル: {project_file}")
        print(f"🎧 ミックス音声: {mixed_audio}")
    else:
        # 通常の処理（台本生成から）
        generator.generate(args.theme, args.episode_name)


if __name__ == "__main__":
    main()
