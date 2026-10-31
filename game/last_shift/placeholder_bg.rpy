init python:
    
    def _build_demo_background(width=3200, height=1080):
        """
        用 Ren'Py 內建的 Solid / Text 拼出一張測試背景，不需要任何美術檔案。

        每 400px 畫一條深色直帶並標上該處的 X 座標，
        這樣鏡頭有沒有在動一眼就看得出來，
        也方便你直接讀出想放 hotspot 的位置該填多少 x。
        """
        # Composite 的參數格式：(整張圖的尺寸), (位置), 圖層, (位置), 圖層, ...
        parts = [(width, height)]

        # 底色
        parts += [(0, 0), Transform(Solid("#2c3e50"), xysize=(width, height))]

        # 每 400px 一條色帶 + 座標數字
        for x in range(0, width, 400):
            parts += [(x, 0), Transform(Solid("#34495e"), xysize=(200, height))]
            parts += [(x + 16, 24), Text(str(x), size=40, color="#7f8c8d")]

        return Composite(*parts)