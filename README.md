# Moon Distance

指定した年と月について、月と地球の距離を1日ごとに計算する Python コードです。

## 設計方針

- 近似式ではなく、JPL エフェメリスを読む `Skyfield` を使う
- 1日ごとの値は「各日の指定時刻」でサンプリングする
- 日付の解釈はタイムゾーン付き `datetime` で扱う
- 計算モジュールと CLI を分離し、後段の `matplotlib` 描画を追加しやすくする

## 実装の責務分離

- `build_local_datetimes()`: 対象月の日付配列を作る
- `calculate_daily_moon_distance()`: エフェメリス読み込みと距離計算を行う
- `extract_plot_data()`: 描画用にサンプル時刻配列と距離配列を取り出す
- `main.py`: CLI 引数を受け取り、表形式で出力する

## 使い方

```bash
pip install -r requirements.txt
```

```bash
python main.py 2026 5 --timezone Asia/Tokyo --hour 0 --minute 0
```

初回実行時は `data/` 配下にエフェメリスファイルを取得します。ネットワークを使わずに実行したい場合は、先に `data/de421.bsp` を配置してください。
