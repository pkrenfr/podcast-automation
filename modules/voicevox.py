#!/usr/bin/env python3
"""
VOICEVOX音声合成モジュール
"""
import requests
import json
import time
from pathlib import Path
from typing import List, Dict


class VoicevoxClient:
    """VOICEVOXエンジンとの通信クライアント"""
    
    # スピーカーID定義
    SPEAKERS = {
        "zundamon": 3,      # ずんだもん（ノーマル）
        "metan": 2,         # 四国めたん（ノーマル）
    }
    
    def __init__(self, base_url="http://localhost:50021"):
        """
        初期化
        
        Args:
            base_url: VOICEVOX EngineのベースURL
        """
        self.base_url = base_url.rstrip('/')
    
    def is_available(self) -> bool:
        """VOICEVOXが利用可能かチェック"""
        try:
            response = requests.get(f"{self.base_url}/version", timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_speakers(self) -> List[Dict]:
        """利用可能なスピーカー一覧を取得"""
        try:
            response = requests.get(f"{self.base_url}/speakers")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ スピーカー一覧取得失敗: {e}")
            return []
    
    def synthesize(
        self,
        text: str,
        speaker: str = "zundamon",
        output_path: Path = None,
        speed_scale: float = 1.0,
        pitch_scale: float = 0.0,
        intonation_scale: float = 1.0,
        timeout: int = 30
    ) -> Path:
        """
        テキストを音声合成
        
        Args:
            text: 合成するテキスト
            speaker: スピーカー名（zundamon, metan）
            output_path: 出力先パス（省略時は一時ファイル）
            speed_scale: 話速（0.5〜2.0）
            pitch_scale: 音高（-0.15〜0.15）
            intonation_scale: 抑揚（0.0〜2.0）
            timeout: タイムアウト（秒）
        
        Returns:
            Path: 生成されたWAVファイルのパス
        """
        speaker_id = self.SPEAKERS.get(speaker.lower())
        if speaker_id is None:
            raise ValueError(f"未知のスピーカー: {speaker}")
        
        # Step 1: AudioQuery取得
        params = {
            "text": text,
            "speaker": speaker_id
        }
        
        try:
            query_response = requests.post(
                f"{self.base_url}/audio_query",
                params=params,
                timeout=timeout
            )
            query_response.raise_for_status()
            query_data = query_response.json()
            
            # パラメータ調整
            query_data["speedScale"] = speed_scale
            query_data["pitchScale"] = pitch_scale
            query_data["intonationScale"] = intonation_scale
            
        except requests.RequestException as e:
            print(f"❌ AudioQuery取得失敗: {e}")
            raise
        
        # Step 2: 音声合成
        try:
            synthesis_response = requests.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker_id},
                json=query_data,
                timeout=timeout
            )
            synthesis_response.raise_for_status()
            
        except requests.RequestException as e:
            print(f"❌ 音声合成失敗: {e}")
            raise
        
        # Step 3: WAVファイル保存
        if output_path is None:
            output_path = Path(f"/tmp/voicevox_{speaker}_{hash(text)}.wav")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(synthesis_response.content)
        
        return output_path
    
    def synthesize_segments(
        self,
        segments: List[Dict],
        output_dir: Path,
        speed_scale: float = 1.0,
        pitch_scale: float = 0.0,
        intonation_scale: float = 1.0,
        chunk_size: int = 10,
        cooldown_sec: float = 0.5
    ) -> List[Path]:
        """
        複数セグメントを一括音声合成（チャンク処理でCPU負荷軽減）
        
        Args:
            segments: セグメントリスト [{"speaker": "zundamon", "text": "..."}, ...]
            output_dir: 出力ディレクトリ
            speed_scale: 話速（デフォルト: 1.0）
            pitch_scale: 音高（デフォルト: 0.0）
            intonation_scale: 抑揚（デフォルト: 1.0）
            chunk_size: チャンクサイズ（デフォルト: 10）
            cooldown_sec: チャンク間のクールダウン時間（秒）
        
        Returns:
            List[Path]: 生成されたWAVファイルのパスリスト
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        voice_files = []
        total = len(segments)
        
        print(f"  📊 合計{total}セグメントを{chunk_size}個ずつ処理")
        
        # チャンクに分割して処理
        for chunk_idx in range(0, total, chunk_size):
            chunk_end = min(chunk_idx + chunk_size, total)
            chunk = segments[chunk_idx:chunk_end]
            chunk_num = chunk_idx // chunk_size + 1
            total_chunks = (total + chunk_size - 1) // chunk_size
            
            print(f"\n  🔄 チャンク {chunk_num}/{total_chunks} (#{chunk_idx+1}〜#{chunk_end})")
            
            for i, segment in enumerate(chunk):
                global_idx = chunk_idx + i
                speaker = segment.get("speaker", "zundamon")
                text = segment["text"]
                
                output_path = output_dir / f"{global_idx:03d}_{speaker}.wav"
                
                # 進捗表示
                text_preview = text[:40] + ('...' if len(text) > 40 else '')
                print(f"    [{global_idx+1:2d}/{total}] {speaker:8s}: {text_preview}")
                
                try:
                    self.synthesize(
                        text=text,
                        speaker=speaker,
                        output_path=output_path,
                        speed_scale=speed_scale,
                        pitch_scale=pitch_scale,
                        intonation_scale=intonation_scale
                    )
                    voice_files.append(output_path)
                    
                except Exception as e:
                    print(f"    ❌ 失敗: {e}")
                    continue
            
            # チャンク間でクールダウン（CPU負荷軽減）
            if chunk_end < total:
                print(f"  ⏸️ クールダウン ({cooldown_sec}秒)...")
                time.sleep(cooldown_sec)
        
        success_rate = len(voice_files) / total * 100 if total > 0 else 0
        print(f"\n  ✅ 完了: {len(voice_files)}/{total} ({success_rate:.1f}%)")
        
        return voice_files
