#!/usr/bin/env python3
"""
原稿生成モジュール - 美術作品のリサーチと台本作成
"""
import os
import json
from pathlib import Path
from typing import Dict, List


class PodcastResearcher:
    """美術作品のリサーチと台本生成"""
    
    def __init__(self):
        """初期化"""
        self.session_key = os.getenv('CLAWDBOT_SESSION_KEY', 'agent:main:discord:channel:1468631923701186562')
    
    def research_topic(self, theme: str) -> Dict:
        """
        テーマについてリサーチ
        
        Args:
            theme: 美術作品のテーマ（例: "モネの睡蓮"）
        
        Returns:
            Dict: リサーチ結果
        """
        print(f"  🔍 テーマをリサーチ中: {theme}")
        
        # TODO: 実際にはweb_searchを使ってリサーチ
        # 今は簡易版として構造化データを返す
        
        research_data = {
            "theme": theme,
            "artist": "クロード・モネ",
            "period": "1890年代後半〜1926年",
            "background": "モネは晩年、ジヴェルニーの自宅の庭に造った睡蓮の池を繰り返し描きました。",
            "key_points": [
                "光の変化を捉えた印象派の集大成",
                "連作として250点以上制作",
                "晩年の白内障と色彩の変化"
            ],
            "interesting_facts": [
                "池の睡蓮は日本の浮世絵に影響を受けて植えられた",
                "最大の作品は2m x 6m以上の大作",
                "死の直前まで筆を握り続けた"
            ]
        }
        
        return research_data
    
    def generate_script(self, theme: str, research_data: Dict = None, episode_length: str = "medium") -> Dict:
        """
        台本を生成
        
        Args:
            theme: エピソードのテーマ
            research_data: リサーチ結果（省略時は自動リサーチ）
            episode_length: エピソードの長さ（short/medium/long）
        
        Returns:
            Dict: 台本データ
        """
        print(f"  ✍️ 台本を生成中...")
        
        # リサーチデータがなければリサーチ
        if research_data is None:
            research_data = self.research_topic(theme)
        
        # 台本のプロンプトを構築
        prompt = self._build_script_prompt(theme, research_data, episode_length)
        
        # Claude APIで台本生成（Clawdbot経由）
        script_text = self._generate_with_claude(prompt)
        
        # 台本をパース
        script = self._parse_script(script_text)
        
        print(f"  ✅ 台本生成完了: {len(script['segments'])}セグメント")
        
        return script
    
    def _build_script_prompt(self, theme: str, research_data: Dict, episode_length: str) -> str:
        """台本生成用のプロンプトを構築"""
        
        length_guide = {
            "short": "3〜5分程度（1000〜1500文字）",
            "medium": "8〜10分程度（2500〜3500文字）",
            "long": "15〜20分程度（5000〜7000文字）"
        }
        
        prompt = f"""あなたは美術ポッドキャスト台本作家として、楽しく学べる対話形式の台本を作成してください。

# テーマ
{theme}

# リサーチ情報
{json.dumps(research_data, ensure_ascii=False, indent=2)}

# 台本の要件
- 長さ: {length_guide.get(episode_length, "8〜10分程度")}
- 形式: 生徒と先生の対話形式
- 雰囲気: 教育的だけど堅苦しくない、楽しい掛け合い
- 構成:
  1. イントロ（軽い掛け合いから入る）
  2. 作品の紹介（ずんだもんの素朴な質問から）
  3. 背景・エピソード（面白いエピソード重視）
  4. 技法・特徴（分かりやすく、時々ずんだもんがボケる）
  5. エンディング（印象に残るまとめ）

# キャラクター設定

**ずんだもん（生徒役）:**
- 元気で好奇心旺盛な小学生〜中学生くらいのイメージ
- 視聴者の代弁者として、素朴な疑問を投げかける
- たまに現実世界の例えでボケる（例：「それってコンビニのおにぎりみたいな感じ？」）
- 語尾に「〜なのだ」「〜のだ！」を使う
- 驚いたり、感心したり、リアクションが豊か
- たまに的外れなことを言って、めたんにツッコまれる
- 白々しい茶番も厭わない

**四国めたん（先生役）:**
- 優しく丁寧な美術の先生
- 分かりやすく、でも深い知識で解説
- ずんだもんのボケに優しくツッコむ
- 時々「それは違いますね（笑）」と笑いながら訂正
- 丁寧語だけど堅苦しくない
- 例え話やエピソードを交えて説明

# 対話の雰囲気
- **教育番組風だけど親しみやすい**
- 白々しい茶番も大歓迎（「え〜！知らなかったのだ〜！」みたいな）
- ずんだもんのボケ → めたんが優しくツッコむ → 正しい情報、の流れ
- たまにずんだもんが意外と鋭いことを言う
- 視聴者が「自分も同じこと思った！」と思える質問

# 悪い例（避けるべき）
❌ ずんだもん: 「睡蓮について教えてください」（受動的すぎる）
❌ めたん: 「それは1890年代に...」（説明が長すぎて一方的）

# 良い例
✅ ずんだもん: 「ねえねえめたん！モネって人は睡蓮ばっかり描いてたって聞いたのだ！飽きなかったのかなぁ？」
✅ めたん: 「ふふ、良い質問ですね。実は、モネにとって睡蓮は毎回違って見えたんですよ」
✅ ずんだもん: 「え！？同じ池なのに！？それってコンビニに毎日行っても飽きないみたいな感じ？」
✅ めたん: 「例えは...まあ近いですね（笑）。光や季節で、池の表情は刻々と変わりますから」

# 出力フォーマット
以下のJSON形式で出力してください：

```json
{{
  "title": "エピソードタイトル（キャッチーに）",
  "description": "エピソードの説明文（2〜3行、視聴者が興味を持つように）",
  "segments": [
    {{"speaker": "zundamon", "text": "台詞"}},
    {{"speaker": "metan", "text": "台詞"}},
    ...
  ]
}}
```

重要: 
- 純粋なJSON形式で出力し、余計な説明文は含めない
- segmentsは最低20個以上（自然な掛け合いのため）
- ずんだもんとめたんが交互に話すのが基本だけど、連続もOK
- ずんだもんのボケは2〜3回入れる
- 白々しい茶番も1〜2回入れる
"""
        
        return prompt
    
    def _generate_with_claude(self, prompt: str) -> str:
        """
        Claude APIで台本生成（Clawdbot経由）
        
        現在はダミーデータを返す。
        本番では --script-json オプションで事前生成した台本を渡すこと。
        
        Args:
            prompt: 台本生成プロンプト
        
        Returns:
            str: ダミー台本テキスト（JSON形式）
        """
        print(f"  ⚠️ Claude API連携は未実装です")
        print(f"  💡 ヒント: --script-json オプションで台本を直接指定できます")
        print(f"  📝 例: python main.py 'テーマ' --script-json script.json")
        print(f"\n  🔄 ダミーデータ（モネの睡蓮）を使用します...\n")
        
        return self._get_dummy_script()
    
    def _get_dummy_script(self) -> str:
        """ダミー台本を返す"""
        
        # ダミーの台本（新しいスタイル）
        dummy_script = {
            "title": "モネの睡蓮 ー なぜ同じ池を250回も描いたの？",
            "description": "印象派の巨匠モネが、晩年に睡蓮ばかり描き続けた理由とは？ずんだもんの素朴な疑問から、モネの驚くべき秘密が明らかに！",
            "segments": [
                {"speaker": "zundamon", "text": "ねえねえめたん！今日は何を勉強するのだ？"},
                {"speaker": "metan", "text": "今日は、クロード・モネの「睡蓮」について学びましょう。"},
                {"speaker": "zundamon", "text": "睡蓮！あの水に浮かぶ花だよね！知ってるのだ！"},
                {"speaker": "metan", "text": "そうですね。でも、モネはこの睡蓮を何枚描いたと思いますか？"},
                {"speaker": "zundamon", "text": "えーっと...10枚くらい？"},
                {"speaker": "metan", "text": "なんと、250枚以上なんです。"},
                {"speaker": "zundamon", "text": "に、にひゃくごじゅうまい！？そんなに！？飽きなかったのかなぁ..."},
                {"speaker": "metan", "text": "良い質問ですね。実は、モネにとって睡蓮は毎回違って見えたんですよ。"},
                {"speaker": "zundamon", "text": "え！？同じ池なのに！？それってコンビニに毎日行っても毎回新しいおにぎりが出てる感じ？"},
                {"speaker": "metan", "text": "例えは...まあ近いですね（笑）。朝の光、昼の光、夕暮れの光。季節や天気でも、池の表情は刻々と変わりますから。"},
                {"speaker": "zundamon", "text": "なるほど！光が違うと全然違う絵になるのだ！"},
                {"speaker": "metan", "text": "その通り！これこそが印象派の真髄なんです。モネは「変化する時間」を描こうとしたんですね。"},
                {"speaker": "zundamon", "text": "でもでも、その池ってどこにあったのだ？美術館？"},
                {"speaker": "metan", "text": "いいえ、モネの自宅の庭です。しかも、池そのものをモネ自身が造ったんですよ。"},
                {"speaker": "zundamon", "text": "ええ！？自分で池を造っちゃったのだ！？それってめっちゃお金持ちじゃないと無理なのでは..."},
                {"speaker": "metan", "text": "ふふ、確かにそうですね。モネは晩年、かなり成功した画家でしたから。"},
                {"speaker": "zundamon", "text": "へー！じゃあその池、今でもあるのかなぁ？"},
                {"speaker": "metan", "text": "はい、ジヴェルニーという村に今も残っていて、観光地になっています。"},
                {"speaker": "zundamon", "text": "行ってみたいのだ！ところで、モネって最後まで絵を描いてたの？"},
                {"speaker": "metan", "text": "実は、モネは晩年白内障になって、だんだん見えにくくなっていたんです。"},
                {"speaker": "zundamon", "text": "えっ！目が悪くなっちゃったのだ！？じゃあ絵はもう描けないよね..."},
                {"speaker": "metan", "text": "ところが、モネは白内障になってもなお、描き続けたんです。それどころか、その「見え方の変化」を逆に利用したとも言われています。"},
                {"speaker": "zundamon", "text": "す、すごいのだ...！ハンディキャップを武器にしちゃうなんて、かっこいいのだ！"},
                {"speaker": "metan", "text": "本当にそうですね。実際、後期の作品ほど色彩が大胆になって、抽象的になっていくんです。"},
                {"speaker": "zundamon", "text": "じゃあさ、一番大きい睡蓮の絵ってどのくらいなのだ？ずんだもんサイズ？"},
                {"speaker": "metan", "text": "ずんだもんサイズって何でしょうか（笑）。パリのオランジュリー美術館にある作品は、高さ2メートル、幅6メートル以上の大作ですよ。"},
                {"speaker": "zundamon", "text": "ろくメートル！？うちの部屋より大きいのだ！"},
                {"speaker": "metan", "text": "しかも、部屋全体を囲むように展示されているんです。まるで本当に池のほとりにいるような感覚が味わえます。"},
                {"speaker": "zundamon", "text": "わぁ！絶対見に行くのだ！めたん、今日もありがとうなのだ！"},
                {"speaker": "metan", "text": "こちらこそ。次回も楽しみにしていてくださいね。"},
            ]
        }
        
        return json.dumps(dummy_script, ensure_ascii=False, indent=2)
    
    def _parse_script(self, script_text: str) -> Dict:
        """
        台本テキストをパース
        
        Args:
            script_text: JSON形式の台本テキスト
        
        Returns:
            Dict: パースされた台本
        """
        try:
            # JSONとしてパース
            script = json.loads(script_text)
            return script
        except json.JSONDecodeError as e:
            print(f"  ⚠️ JSONパースエラー: {e}")
            # エラー時はダミーデータを返す
            return {
                "title": "台本生成エラー",
                "description": "台本の生成に失敗しました",
                "segments": [
                    {"speaker": "zundamon", "text": "台本の生成でエラーが発生したのだ..."},
                    {"speaker": "metan", "text": "申し訳ございません。もう一度お試しください。"}
                ]
            }
    
    def save_script(self, script: Dict, output_path: Path) -> Path:
        """
        台本をMarkdownファイルとして保存
        
        Args:
            script: 台本データ
            output_path: 出力先パス
        
        Returns:
            Path: 保存されたファイルのパス
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {script['title']}\n\n")
            f.write(f"> {script['description']}\n\n")
            f.write("---\n\n")
            
            for seg in script['segments']:
                speaker_name = "ずんだもん" if seg['speaker'] == "zundamon" else "四国めたん"
                f.write(f"**{speaker_name}**: {seg['text']}\n\n")
        
        return output_path


if __name__ == "__main__":
    # テスト
    researcher = PodcastResearcher()
    
    print("🔬 PodcastResearcher テスト")
    print("\n--- リサーチテスト ---")
    research = researcher.research_topic("モネの睡蓮")
    print(json.dumps(research, ensure_ascii=False, indent=2))
    
    print("\n--- 台本生成テスト ---")
    script = researcher.generate_script("モネの睡蓮", research)
    print(f"✅ タイトル: {script['title']}")
    print(f"✅ セグメント数: {len(script['segments'])}")
    
    print("\n--- 台本保存テスト ---")
    output = Path("/tmp/test_script.md")
    researcher.save_script(script, output)
    print(f"✅ 保存先: {output}")
