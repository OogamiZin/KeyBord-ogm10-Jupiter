# ファームウェア（QMK / Vial）

[← トップページに戻る](../../../README.md)

## 書き込み方法

1. 基板の BOOT ジャンパー（JP1）をショートしたまま USB-C IN にケーブルを接続します。
2. `RPI-RP2` ドライブとしてマウントされたら、ファームウェア（`.uf2`）をドラッグ＆ドロップします。

一度書き込んだ後は、左エンコーダーを押しながら接続（Bootmagic）するか、レイヤー3 の `QK_BOOT` でもブートローダーに入れます。

## Firmware

- QMK / Vial 用のファイルは このフォルダ（`qmk_firmware/keyboards/ogm10_jupiter`） にあります。
- push するたびに GitHub Actions（`.github/workflows/build.yml`、`target.json`）で `ogm10_jupiter_vial.uf2` がビルドされ、Actions の Artifacts からダウンロードできます。
- デフォルトキーマップは仮のものです。Vial で自由に変更してください。Vial のアンロックは左右エンコーダーの同時押しです。
- `keyboard.json` / `vial.json` のキー位置は基板上のスイッチ座標をもとにしています。左端3段目と最下段中央の2キーが 1.5u、ほかは 1u です。Vial 上では左右のエンコーダーを 0.75u 幅で表示しています（左は左端、右は2〜4段目の右端に合わせています）。

## Build workflow

ファームウェアのビルドには [sekigon-gonnoc/vial-keymap-c-editor](https://github.com/sekigon-gonnoc/vial-keymap-c-editor) の再利用可能ワークフローを使っています。
