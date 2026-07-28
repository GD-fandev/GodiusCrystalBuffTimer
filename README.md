# Godius Crystal Buff Timer

## 日本語

Godius EW 用の 結晶バフタイマーです。
ゲーム画面上の 氷の結晶・炎の結晶 のバフアイコンを検出し、残り時間をオーバーレイで表示します。

ファイルのダウンロード: [リリースページ](https://github.com/GD-fandev/GodiusCrystalBuffTimer/releases/tag/v1.0.0)

検出には少し時間がかかるため、タイマー開始時の表示は通常 598 秒前後になります。
このツールは非公式のファンメイドツールです。キャラクター操作、クライアント改変、パケット操作は行いません。

### 使い方

1. Godius EW を起動します。
2. `GodiusCrystalBuffTimer.exe` を起動します。
3. 必要に応じて検出位置を調整します。
4. 氷の結晶、または炎の結晶のバフアイコンが検出されると、対応するアイコンでタイマーが自動で開始します。

### 操作

- `F10`: 検出位置調整モードのオン / オフ
- `テンキー +` / `テンキー -`: 調整モード中に検出範囲のサイズを変更
- `QUIT`: 終了
- `Ctrl + 左ドラッグ`: タイマー表示、または赤い検出枠を移動

## 한국어

Godius EW용 Crystal Buff 타이머입니다.
게임 화면의 얼음의 결정 / 불의 결정 버프 아이콘을 감지하고, 남은 시간을 오버레이로 표시합니다.

파일 다운로드: [릴리스 페이지](https://github.com/GD-fandev/GodiusCrystalBuffTimer/releases/tag/v1.0.0)

감지에 약간의 시간이 걸리기 때문에 타이머 시작 시 표시는 보통 598초 전후입니다.
이 도구는 비공식 팬 제작 도구입니다. 캐릭터 조작, 클라이언트 수정, 패킷 조작을 하지 않습니다.

### 사용 방법

1. Godius EW를 실행합니다.
2. `GodiusCrystalBuffTimer.exe`를 실행합니다.
3. 필요하면 감지 위치를 조정합니다.
4. 얼음의 결정 또는 불의 결정 버프 아이콘이 감지되면 해당 아이콘으로 타이머가 자동 시작됩니다.

### 조작

- `F10`: 감지 위치 조정 모드 켜기 / 끄기
- `Numpad +` / `Numpad -`: 조정 모드에서 감지 범위 크기 변경
- `QUIT`: 종료
- `Ctrl + 왼쪽 드래그`: 타이머 표시 또는 빨간 감지 박스 이동

## English

Godius Crystal Buff Timer is a buff timer overlay for Godius EW.
It detects the Ice Crystal / Fire Crystal buff icon on the game screen and displays the remaining time as an overlay.

Download files: [Release page](https://github.com/GD-fandev/GodiusCrystalBuffTimer/releases/tag/v1.0.0)

Because detection takes a moment, the timer usually starts at around 598 seconds.
This is an unofficial fan-made tool. It does not control your character, modify the client, or touch packets.

### How To Use

1. Start Godius EW.
2. Run `GodiusCrystalBuffTimer.exe`.
3. Adjust the detection position if needed.
4. When the Ice Crystal or Fire Crystal buff icon is detected, the timer starts automatically with the matching display icon.

### Controls

- `F10`: enter or leave detection-position adjustment mode
- `Numpad +` / `Numpad -`: resize the detection area while adjustment mode is active
- `QUIT`: exit the app
- `Ctrl + left drag`: move the timer overlay or the red detection box

## Source And Build

```bat
pip install -r requirements.txt
python source\godius_buff_timer.py
```

For EXE build instructions, see [BUILD.md](BUILD.md).

## License / ライセンス / 라이선스

### 日本語

このリポジトリのソースコードは MIT License で公開されています。
ゲーム名、アイコン、バフ画像など Godius 関連の素材は PlayinWorld に権利があり、MIT License の対象外です。
Copyright (c) PlayinWorld. All rights reserved.
権利者から要請があった場合、関連素材を削除します。

### 한국어

이 저장소의 소스 코드는 MIT License로 공개됩니다.
게임명, 아이콘, 버프 이미지 등 Godius 관련 소재의 권리는 PlayinWorld에 있으며, MIT License 적용 대상이 아닙니다.
Copyright (c) PlayinWorld. All rights reserved.
권리자의 요청이 있을 경우 관련 소재를 제거합니다.

### English

The source code in this repository is licensed under the MIT License.
Game names, icons, buff images, and other Godius-related assets are property of PlayinWorld and are not covered by the MIT License.
Copyright (c) PlayinWorld. All rights reserved.
If requested by the rights holder, related assets will be removed.
