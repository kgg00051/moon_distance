# Moon Distance

指定した年、または年と月について、月と地球の距離を1日ごとに計算する Python コードです。

## 設計方針

- 近似式ではなく、JPL エフェメリスを読む `Skyfield` を使う
- 1日ごとの値は「各日の指定時刻」でサンプリングする
- 月未指定なら 1 年分の日次距離をまとめて計算する
- 日付の解釈はタイムゾーン付き `datetime` で扱う
- 計算モジュールと CLI を分離し、`matplotlib` で PNG グラフも生成する

## 実装の責務分離

- `build_local_datetimes()`: 対象月または対象年の日付配列を作る
- `calculate_daily_moon_distance()`: 対象月または対象年のエフェメリス読み込みと距離計算を行う
- `extract_plot_data()`: 描画用にサンプル時刻配列と距離配列を取り出す
- `main.py`: CLI 引数を受け取り、CSV 出力とグラフ保存を行う

## 使い方

```bash
pip install -r requirements.txt
```

```bash
python main.py 2026 5 --timezone Asia/Tokyo --hour 0 --minute 0
```

```bash
python main.py 2026 --timezone Asia/Tokyo --hour 0 --minute 0
```

既定では CSV を標準出力に出しつつ、グラフ画像を `output/moon_distance_2026_05.png` や `output/moon_distance_2026.png` に保存します。

```bash
python main.py 2026 5 --plot-output charts/may-2026.png
```

```bash
python main.py 2026 5 --show-plot
```

```bash
python main.py 2026 5 --no-plot
```

初回実行時は `data/` 配下にエフェメリスファイルを取得します。ネットワークを使わずに実行したい場合は、先に `data/de421.bsp` を配置してください。
