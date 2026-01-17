# VOICEPEAK to Discord Transmitter

VOICEPEAKで生成した音声を、仮想オーディオデバイス経由でDiscordのマイク入力として送信するためのデスクトップアプリケーションです。

## 前提条件

1. **VOICEPEAK**: インストールされており、CLI（`voicepeak.exe`）が利用可能であること。
2. **仮想オーディオデバイス**: [VB-CABLE](https://vb-audio.com/Cable/) 等の仮想ケーブルソフトがインストールされていること。
3. **Python 3.x**: インストールされていること。

## セットアップ手順 (仮想環境の利用)

システム全体のPython環境を汚さないよう、仮想環境（venv）を作成して実行することを推奨します。

### 1. 仮想環境の作成

プロジェクトのルートディレクトリ（`app.py` がある場所）でターミナルを開き、以下のコマンドを実行します。

```powershell
# 仮想環境 'venv' を作成
python -m venv venv
```

### 2. 仮想環境の有効化

```powershell
# Windows PowerShellの場合
.\venv\Scripts\Activate.ps1

# Windows コマンドプロンプトの場合
.\venv\Scripts\activate.bat
```
※有効化されると、プロンプトの先頭に `(venv)` と表示されます。

### 3. ライブラリのインストール

仮想環境が有効な状態で、必要なパッケージをインストールします。

```powershell
pip install sounddevice soundfile numpy
```

## アプリの使い方

### 1. アプリの起動

仮想環境が有効な状態で実行します。

```powershell
python app.py
```

### 2. アプリの設定

1.  **VOICEPEAK Path**: `voicepeak.exe` の場所を指定します（例: `C:\Program Files\VOICEPEAK\voicepeak.exe`）。
2.  **出力デバイス**: 「更新」ボタンを押し、ドロップダウンから **「CABLE Input (VB-Audio Virtual Cable)」** を選択します。
3.  **ナレーター名**: 使用したいナレーター名を入力・選択します（例: `Japanese Female 1`）。

### 3. 送信テスト

1.  テキストボックスに何か入力して「送信」ボタンを押すか、Enterキーを押します。
2.  ステータスが「再生中」になり、完了すれば成功です。
    *   ※この時点では自分には聞こえませんが、仮想デバイスに信号が送られています。

## Discord側の設定

音声を実際にDiscordで相手に聞かせるには、Discord側の設定が必要です。

1.  Discordの「ユーザー設定」>「音声・ビデオ」を開きます。
2.  **入力デバイス** を **「CABLE Output (VB-Audio Virtual Cable)」** に変更します。
3.  （推奨）Discordの「入力感度」を自動調整にするか、仮想ケーブルの音量が十分であることを確認してください。
4.  （推奨）ノイズ抑制などの機能が音声をカットしてしまう場合があるため、うまくいかない場合は「ノイズ抑制」をオフにしてみてください。

## トラブルシューティング

- **VOICEPEAKのエラーが出る**: パスが正しいか、コンソール版が正常に動作するか確認してください。
- **デバイスが見つからない**: VB-CABLEが正しくインストールされているか確認し、アプリの「更新」ボタンを押してください。
- **Discordに音が載らない**: Discordの入力デバイス設定が正しいか、またPCの音声設定でマイクとして認識されているか確認してください。
