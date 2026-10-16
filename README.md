# ogm10-Jupiter

RP2040 と USB ハブ（CH334F）を基板に載せた、43キー + ロータリーエンコーダー 2個の一体型キーボードです。
基板・プレート・ファームウェアはすべて EasyEDA / QMK で一から設計しています。

## Specs

| 項目 | 内容 |
|---|---|
| キー数 | 43キー + ロータリーエンコーダー 2個（左右・プッシュスイッチ付き） |
| スイッチ | Kailh Choc V2（ホットスワップソケット） |
| MCU | RP2040（基板直付け） |
| フラッシュ | W25Q128JVSIQ（128Mbit / 16MB） |
| USB | Type-C 入力 ×1 + USB ハブ出力（Type-C）×3 |
| マトリクス | 4行 × 12列（COL2ROW、エンコーダーのプッシュもマトリクス内） |
| 基板サイズ | 約 227.4 mm × 76.2 mm |
| 取り付け穴 | φ2.2 mm × 8（M2） |
| ファームウェア | QMK / Vial |

### USB ハブ

- 上流の USB-C IN から CH334F（4ポートハブ）に入り、ポート1〜3 を USB-C OUT1〜3、ポート4 を RP2040 に接続しています。
- 入力は ESD 保護（USBLC6-2SC6）と 2A ポリスイッチを通り、出力側の 5V ラインには 22µF ×4 のバルクコンデンサ、各出力ポートの CC には 56kΩ プルアップ（Rp）が付いています。
- 出力ポートの合計電流は、上流のポートが供給できる範囲（一般的なPCのポートなら 500mA〜900mA 程度）に収まるように使ってください。

## Parts List

### 自分で用意するもの

| Part | Quantity |
|---|---|
| Choc V2 スイッチ | 43 |
| キーキャップ（Choc 用） | 43 |
| ロータリーエンコーダー用ノブ | 2 |
| USB Type-C ケーブル | 1〜 |
| M2 ネジ・スペーサー | 8 |

### 基板実装部品

| Ref | Part | Package | LCSC | Qty |
|---|---|---|---|---|
| U2 | RP2040 | LQFN-56 | C2040 | 1 |
| U3 | W25Q128JVSIQ（QSPI Flash） | SOIC-8 | C97521 | 1 |
| U1 | CH334F（USB 2.0 ハブ） | QFN-24 | C5187527 | 1 |
| U4 | XC6206P332MR（3.3V LDO） | SOT-23 | C5446 | 1 |
| X2 | 12MHz 水晶 ABM8-272-T3（RP2040 用） | 3225 | C20625731 | 1 |
| X1 | 12MHz 水晶 X322512MSB4SI（ハブ用） | 3225 | C9002 | 1 |
| D1 | USBLC6-2SC6（ESD 保護） | SOT-23-6 | C7519 | 1 |
| F1 | 2A PTC ヒューズ SMD1206P200TF | 1206 | C20988 | 1 |
| USBC1–4 | TYPE-C-31-M-12 | SMD | C165948 | 4 |
| ENC1, ENC2 | ALPS EC11E18244A5（18パルス / 36クリック） | THT | C255515 | 2 |
| JP1 | 2P ピンヘッダ（BOOT 用） | 2.54mm | C492401 | 1 |
| LED1 | 電源 LED | 0603 | C72043 | 1 |
| SW3–SW45 | Choc ホットスワップソケット CPG135001S30 | SMD | C5333465 | 43 |
| D2–D46 | 1N4148W | SOD-123F | C81598 | 45 |
| R1, R2 | 5.1kΩ（上流 CC プルダウン） | 0603 | C23186 | 2 |
| R5–R10 | 56kΩ（下流 CC プルアップ） | 0603 | C23206 | 6 |
| R12, R13 | 27Ω（USB D+/D-） | 0603 | C25190 | 2 |
| R3 | 1kΩ（LED） | 0603 | C21190 | 1 |
| R4 | 10kΩ（ハブ PSELF） | 0603 | C25804 | 1 |
| R11, R15 | 1kΩ（XOUT 直列 / BOOT） | 0402 | C11702 | 2 |
| R14 | 10kΩ（RUN プルアップ） | 0402 | C25744 | 1 |
| C1, C25, C26 | 10µF | 0805 | C15850 | 3 |
| C5–C8 | 22µF | 0805 | C45783 | 4 |
| C3, C21, C22 | 1µF | 0603 | C15849 | 3 |
| C2, C4, C9 | 100nF | 0603 | C14663 | 3 |
| C10, C13–C20, C23, C24 | 100nF | 0402 | C1525 | 11 |
| C11, C12 | 15pF | 0402 | C1548 | 2 |

## Pin Assignment（RP2040）

| 機能 | GPIO |
|---|---|
| ROW0–ROW3 | GP6, GP7, GP8, GP9 |
| COL0–COL5 | GP0, GP1, GP2, GP3, GP4, GP5 |
| COL6–COL11 | GP18, GP19, GP20, GP21, GP22, GP23 |
| エンコーダー1（左） A / B | GP12 / GP13（プッシュ = マトリクス R0C0） |
| エンコーダー2（右） A / B | GP24 / GP25（プッシュ = マトリクス R0C11） |
| 未使用 | GP10, GP11, GP14–GP17, GP26–GP29 |
| USB D+ / D- | ハブ経由（CH334F ポート4） |

## 書き込み方法

1. 基板の BOOT ジャンパー（JP1）をショートしたまま USB-C IN にケーブルを接続します。
2. `RPI-RP2` ドライブとしてマウントされたら、ファームウェア（`.uf2`）をドラッグ＆ドロップします。

一度書き込んだ後は、左エンコーダーを押しながら接続（Bootmagic）するか、レイヤー3 の `QK_BOOT` でもブートローダーに入れます。

## Firmware

- QMK / Vial 用のファイルは [qmk_firmware/keyboards/ogm10_jupiter](qmk_firmware/keyboards/ogm10_jupiter) にあります。
- push するたびに GitHub Actions（`.github/workflows/build.yml`、`target.json`）で `ogm10_jupiter_vial.uf2` がビルドされ、Actions の Artifacts からダウンロードできます。
- デフォルトキーマップは仮のものです。Vial で自由に変更してください。Vial のアンロックは左右エンコーダーの同時押しです。
- `keyboard.json` / `vial.json` のキー位置は基板上のスイッチ座標をもとにしています。左端3段目と最下段中央の2キーが 1.5u、ほかは 1u です。Vial 上の見やすさのため、左エンコーダーは 0.75u 幅で表示し、2〜4段目を右に 0.25u ずらしています（基板の実配置とは異なります）。

## Files

| パス | 内容 |
|---|---|
| `pcb/ogm10-Jupiter-pcb.json` | メイン基板（EasyEDA Standard ソース） |
| `pcb/ogm10-Jupiter-schematic.json` | 回路図（EasyEDA Standard ソース） |
| `plate/ogm10-Jupiter-top-plate.json` | トッププレート（EasyEDA Standard ソース） |
| `plate/ogm10-Jupiter-bottom-plate.json` | ボトムプレート（EasyEDA Standard ソース） |
| `qmk_firmware/` | QMK / Vial ファームウェア |

EasyEDA Standard の「ファイル > 開く > EasyEDA ソース」で各 JSON を読み込めます。

## Build workflow

ファームウェアのビルドには [sekigon-gonnoc/vial-keymap-c-editor](https://github.com/sekigon-gonnoc/vial-keymap-c-editor) の再利用可能ワークフローを使っています。
