# ファームウェア（QMK / Vial）

[← トップページに戻る](../../../README.md)

## 書き込み方法

1. 基板の BOOT ジャンパー（JP1）をショートしたまま USB-C IN にケーブルを接続します。
2. `RPI-RP2` ドライブとしてマウントされたら、ファームウェア（`.uf2`）をドラッグ＆ドロップします。

一度書き込んだ後は、左エンコーダーを押しながら接続（Bootmagic）するか、左右のエンコーダーを押し込んだまま Backspace の位置のキーを押しても、ブートローダーに入れます。

左エンコーダーを押し込んだまま右下のキー（レイヤー 0 では →）を押すと、Chrome で[設定ツール](https://oogamizin.github.io/KeyBord.ogm10-Jupiter/)を開きます。

## Firmware

- QMK / Vial 用のファイルは このフォルダ（`qmk_firmware/keyboards/ogm10_jupiter`） にあります。
- push するたびに GitHub Actions（`.github/workflows/build.yml`、`target.json`）で `ogm10_jupiter_vial.uf2` がビルドされ、Actions の Artifacts からダウンロードできます。
- デフォルトキーマップは仮のものです。[設定ツール](https://oogamizin.github.io/KeyBord.ogm10-Jupiter/)か Vial で自由に変更してください。アンロックは Q と P の位置のキーの同時長押しです。
- `keyboard.json` / `vial.json` のキー位置は基板上のスイッチ座標をもとにしています。左端3段目と最下段中央の2キーが 1.5u、ほかは 1u です。Vial 上では左右のエンコーダーを 0.75u 幅で表示しています（左は左端、右は2〜4段目の右端に合わせています）。

## レイヤー状態の通知（表示ツール向け）

ファームウェアは、現在のレイヤーを Raw HID で知らせる専用コマンドを持っています。[設定ツール](../../../docs/README.md)のレイヤー表示が、今のレイヤーのキー割り当てを画面に出すために使います。

- PC からキーボードへ `[0xF7, 0x01]` を送ると、現在の状態が返ります。同時に、以後 3 秒間はレイヤーが変わるたびにキーボード側から通知（`[0xF7, 0x02, …]`）が届きます。
- 返る内容は、先頭から順に `0xF7`、種別、版数（1）、最上位レイヤー、`layer_state`（4 バイト、下位から）、`default_layer_state`（4 バイト、下位から）、OS 別のデフォルトレイヤーです。
- ツールを閉じると 3 秒で通知は止まるので、標準の Vial の動作には影響しません。
- `[0xF7, 0x03, 位置(上位), 位置(下位)]` で、その位置から 14 キーぶんの初期設定（keymap.c の割り当て）を返します。位置は `(レイヤー * 行数 + 行) * 列数 + 列` です。`[0xF7, 0x04, レイヤー, エンコーダー]` で、エンコーダーの初期設定（反時計回り、時計回り）を返します。どちらも読むだけで、設定は変えません。

## Build workflow

ファームウェアのビルドには [sekigon-gonnoc/vial-keymap-c-editor](https://github.com/sekigon-gonnoc/vial-keymap-c-editor) の再利用可能ワークフローを使っています。

## ファームウェアの版と公開

- 独自コマンド `[0xF7, 0x05]` に、ビルド日時の文字列（例 `Nov 18 2026 07:05:00`）を返します。ファームウェア内には `JUPFW:` に続けて埋め込んであります。
- main へのプッシュでビルドされたファームウェアは、GitHub Actions の publish ジョブが `docs/firmware/ogm10_jupiter_vial.uf2` と `latest.json` に公開します。設定ツールの「ファーム」から、この版に更新できます。
