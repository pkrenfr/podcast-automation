#!/usr/bin/env python3
"""
音声ミックスモジュール
"""
from pathlib import Path
from typing import List
from pydub import AudioSegment
from pydub.effects import normalize


class AudioMixer:
    """音声ミックス処理"""
    
    def __init__(self, config: dict):
        """
        初期化
        
        Args:
            config: 設定辞書（config.yamlのaudio/bgmセクション）
        """
        self.config = config
        self.sample_rate = config.get('audio', {}).get('sample_rate', 44100)
        self.channels = config.get('audio', {}).get('channels', 2)
        
        self.bgm_volume_db = config.get('bgm', {}).get('volume_reduction_db', -20)
        self.fade_in_ms = config.get('bgm', {}).get('fade_in_ms', 3000)
        self.fade_out_ms = config.get('bgm', {}).get('fade_out_ms', 3000)
    
    def concatenate_voices(self, voice_files: List[Path]) -> AudioSegment:
        """
        音声セグメントを結合
        
        Args:
            voice_files: WAVファイルのパスリスト
        
        Returns:
            AudioSegment: 結合された音声
        """
        print(f"  🔗 {len(voice_files)}個の音声を結合中...")
        
        combined = AudioSegment.empty()
        
        for i, voice_file in enumerate(voice_files):
            if not voice_file.exists():
                print(f"  ⚠️ ファイルが存在しません: {voice_file}")
                continue
            
            segment = AudioSegment.from_wav(str(voice_file))
            
            # ステレオに変換（必要な場合）
            if segment.channels == 1 and self.channels == 2:
                segment = segment.set_channels(2)
            
            # サンプリングレート統一
            if segment.frame_rate != self.sample_rate:
                segment = segment.set_frame_rate(self.sample_rate)
            
            combined += segment
            
            # セグメント間に短い無音を追加（0.3秒）
            if i < len(voice_files) - 1:
                silence = AudioSegment.silent(duration=300)
                combined += silence
        
        print(f"  ✅ 結合完了: {len(combined) / 1000:.1f}秒")
        return combined
    
    def prepare_bgm(self, bgm_file: Path, duration_ms: int) -> AudioSegment:
        """
        BGMを準備（ループ、フェード処理）
        
        Args:
            bgm_file: BGMファイルのパス
            duration_ms: 必要な長さ（ミリ秒）
        
        Returns:
            AudioSegment: 処理済みBGM
        """
        print(f"  🎵 BGM準備中...")
        
        if not bgm_file.exists():
            print(f"  ⚠️ BGMファイルが存在しません: {bgm_file}")
            return AudioSegment.silent(duration=duration_ms)
        
        # BGM読み込み（MP3/WAV対応）
        if bgm_file.suffix.lower() == '.mp3':
            bgm = AudioSegment.from_mp3(str(bgm_file))
        elif bgm_file.suffix.lower() == '.wav':
            bgm = AudioSegment.from_wav(str(bgm_file))
        else:
            print(f"  ⚠️ 非対応の形式: {bgm_file.suffix}")
            return AudioSegment.silent(duration=duration_ms)
        
        # ステレオに変換
        if bgm.channels == 1 and self.channels == 2:
            bgm = bgm.set_channels(2)
        
        # サンプリングレート統一
        if bgm.frame_rate != self.sample_rate:
            bgm = bgm.set_frame_rate(self.sample_rate)
        
        # BGMをループ（必要な長さまで）
        if len(bgm) < duration_ms:
            loops_needed = (duration_ms // len(bgm)) + 1
            bgm = bgm * loops_needed
        
        # 必要な長さにカット
        bgm = bgm[:duration_ms]
        
        # 音量調整
        bgm = bgm + self.bgm_volume_db
        
        # フェードイン/アウト
        bgm = bgm.fade_in(self.fade_in_ms).fade_out(self.fade_out_ms)
        
        print(f"  ✅ BGM準備完了: {len(bgm) / 1000:.1f}秒")
        return bgm
    
    def mix(
        self,
        voice_files: List[Path],
        bgm_file: Path,
        output_path: Path
    ) -> Path:
        """
        音声とBGMをミックス
        
        Args:
            voice_files: 音声ファイルのリスト
            bgm_file: BGMファイル
            output_path: 出力先パス
        
        Returns:
            Path: 出力されたファイルのパス
        """
        print("\n🎛️ 音声ミックス開始...")
        
        # 音声結合
        voice_combined = self.concatenate_voices(voice_files)
        
        # BGM準備
        bgm = self.prepare_bgm(bgm_file, len(voice_combined))
        
        # ミックス
        print("  🎚️ ミックス中...")
        mixed = voice_combined.overlay(bgm)
        
        # 正規化（音量を最大化）
        print("  📊 音量正規化中...")
        mixed = normalize(mixed)
        
        # エクスポート
        print(f"  💾 保存中: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        mixed.export(
            str(output_path),
            format="wav",
            parameters=[
                "-ar", str(self.sample_rate),
                "-ac", str(self.channels)
            ]
        )
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ ミックス完了: {file_size_mb:.1f} MB")
        
        return output_path
    
    def export_mp3(
        self,
        input_path: Path,
        output_path: Path,
        bitrate: str = "192k"
    ) -> Path:
        """
        WAVをMP3に変換
        
        Args:
            input_path: 入力WAVファイル
            output_path: 出力MP3ファイル
            bitrate: ビットレート（例: "192k", "256k"）
        
        Returns:
            Path: 出力されたMP3ファイルのパス
        """
        print(f"\n🎵 MP3エクスポート中...")
        
        audio = AudioSegment.from_wav(str(input_path))
        
        audio.export(
            str(output_path),
            format="mp3",
            bitrate=bitrate,
            parameters=["-q:a", "0"]  # 最高品質
        )
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ MP3変換完了: {file_size_mb:.1f} MB ({bitrate})")
        
        return output_path


if __name__ == "__main__":
    # テスト用
    import yaml
    
    with open("../config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    mixer = AudioMixer(config)
    print("✅ AudioMixerモジュール初期化成功")
