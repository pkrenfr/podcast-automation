#!/usr/bin/env python3
"""
システムリソース監視ユーティリティ
"""
import psutil
import os
from pathlib import Path


class ResourceMonitor:
    """CPU/メモリ使用量を監視"""
    
    def __init__(self, warn_cpu_percent=70.0, warn_memory_percent=80.0):
        """
        初期化
        
        Args:
            warn_cpu_percent: CPU使用率の警告閾値（%）
            warn_memory_percent: メモリ使用率の警告閾値（%）
        """
        self.warn_cpu = warn_cpu_percent
        self.warn_memory = warn_memory_percent
        self.process = psutil.Process(os.getpid())
    
    def check(self, verbose=False):
        """
        現在のリソース使用状況をチェック
        
        Args:
            verbose: 詳細表示
        
        Returns:
            dict: {"cpu": float, "memory": float, "warnings": list}
        """
        # システム全体
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        # このプロセス
        proc_cpu = self.process.cpu_percent()
        proc_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        
        warnings = []
        
        if cpu_percent > self.warn_cpu:
            warnings.append(f"⚠️ CPU使用率が高い: {cpu_percent:.1f}%")
        
        if mem.percent > self.warn_memory:
            warnings.append(f"⚠️ メモリ使用率が高い: {mem.percent:.1f}%")
        
        if verbose or warnings:
            print(f"  📊 リソース: CPU {cpu_percent:.1f}% | メモリ {mem.percent:.1f}% | プロセス {proc_mem:.1f}MB")
            for warning in warnings:
                print(f"  {warning}")
        
        return {
            "cpu_system": cpu_percent,
            "cpu_process": proc_cpu,
            "memory_system": mem.percent,
            "memory_process_mb": proc_mem,
            "warnings": warnings
        }
    
    def wait_if_busy(self, max_wait_sec=30, check_interval=2):
        """
        CPU/メモリが高負荷の場合、負荷が下がるまで待機
        
        Args:
            max_wait_sec: 最大待機時間（秒）
            check_interval: チェック間隔（秒）
        
        Returns:
            bool: 待機した場合True
        """
        import time
        
        waited = False
        total_waited = 0
        
        while total_waited < max_wait_sec:
            stats = self.check(verbose=False)
            
            if stats["cpu_system"] < self.warn_cpu and stats["memory_system"] < self.warn_memory:
                break
            
            if not waited:
                print(f"  ⏳ 高負荷検出。負荷が下がるまで待機中...")
                waited = True
            
            time.sleep(check_interval)
            total_waited += check_interval
        
        if waited:
            if total_waited >= max_wait_sec:
                print(f"  ⚠️ タイムアウト ({max_wait_sec}秒)")
            else:
                print(f"  ✅ 負荷が下がりました（待機時間: {total_waited}秒）")
        
        return waited


def set_low_priority():
    """このプロセスの優先度を下げる（他のプロセスへの影響を軽減）"""
    try:
        # Linuxの場合: nice値を10に設定（デフォルトは0）
        os.nice(10)
        print("  🔽 プロセス優先度を下げました (nice +10)")
        return True
    except (AttributeError, PermissionError) as e:
        print(f"  ⚠️ プロセス優先度変更失敗: {e}")
        return False


if __name__ == "__main__":
    # テスト
    monitor = ResourceMonitor()
    print("📊 リソースモニタリングテスト")
    stats = monitor.check(verbose=True)
    print(f"\n結果: {stats}")
