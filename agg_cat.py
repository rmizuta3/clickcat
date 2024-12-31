import pyxel
import random
import yaml


# 猫表示用のクラス
class CAT:
    def __init__(self, name, xy0, xy1, click_price, x, y, anim_start_time):
        # 種別
        self.name = name
        self.anim0 = xy0  # アニメーション用の座標1
        self.anim1 = xy1  # アニメーション用の座標2
        self.click_price = click_price  # クリックした時の価格

        # 個別
        self.x = x  # 猫のx座標
        self.y = y  # 猫のy座標
        self.anim_start_time = anim_start_time  # アニメーション開始時間(ずらすため)


# 猫出現用のクラス
class CatSpecies:
    def __init__(self, name, xy0, xy1, sell_price, click_price, spawn_time, level):
        self.name = name  # 種別名
        self.anim0 = xy0  # アニメーション用の座標1
        self.anim1 = xy1  # アニメーション用の座標2
        self.sell_price = sell_price  # 販売価格
        self.click_price = click_price  # クリックした時の価格
        self.spawn_time = spawn_time  # 猫の出現間隔
        self.spawn_timer = 0  # 猫の出現タイマー
        self.level = level  # レベル


# クリック時のテキストエフェクト
class TextParticle:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text
        self.vy = -1  # 上に向かって移動する速度
        self.life = 15  # テキストの寿命

    def update(self):
        self.y += self.vy
        self.life -= 1


class APP:
    MAIN = 0  # メイン
    GAMECLEAR = 1  # ゲームクリア

    def __init__(self):
        pyxel.init(128, 128, title="pyxel", fps=30)
        pyxel.load("cat.pyxres")
        # マウスカーソル表示
        pyxel.mouse(True)

        # 設定ファイル(yaml)の読み込み
        with open("./config.yml", "r") as file:
            self.config = yaml.safe_load(file)

        self.init()

        self.max_level = 5

        pyxel.run(self.update, self.draw)

    def init(self):
        self.state = self.MAIN
        self.cats = []
        self.particles = []
        self.money = 0
        self.animation_frame = 0  # アニメーション用のフレームカウンタ
        self.money = 0  # お金の初期化
        self.cat_info = self.config["cat_info"]  # 猫の情報
        self.show_shop = False  # ショップ画面の表示フラグ

        # 猫種別のクラスリストを作成
        self.spawnable_catspecies = []
        for cat_type in self.cat_info.keys():
            if cat_type == "mike":
                level = 1  # 通常猫は最初から出現
            else:
                level = 0
            self.spawnable_catspecies.append(
                CatSpecies(
                    cat_type,
                    self.cat_info[cat_type]["xy0"],
                    self.cat_info[cat_type]["xy1"],
                    self.cat_info[cat_type]["sell_prices"],
                    self.cat_info[cat_type]["click_prices"],
                    self.cat_info[cat_type]["spawn_time"],
                    level,
                )
            )

    def check_click(self, x, y):
        for cat in self.cats:
            cat_x = cat.x
            cat_y = cat.y
            if cat_x <= x <= cat_x + 16 and cat_y <= y <= cat_y + 16:
                click_price = cat.click_price
                self.money += click_price

                # クリック時のテキストエフェクト
                self.particles.append(
                    TextParticle(cat_x, cat_y, f"+{str(click_price)}")
                )
                self.cats.remove(cat)
                break

    def update(self):
        # アニメーションフレームの更新
        self.animation_frame = (self.animation_frame + 1) % 30  # 30フレームでループ

        # ゲームクリア画面での処理
        if self.state == self.GAMECLEAR:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                if 25 <= pyxel.mouse_x <= 65 and 90 <= pyxel.mouse_y <= 100:
                    self.state = self.MAIN  # メイン画面に戻る
                elif 70 <= pyxel.mouse_x <= 110 and 90 <= pyxel.mouse_y <= 100:
                    self.init()  # ゲームをリスタート
                    self.state = self.MAIN
            return

        # 購入ボタンのクリック処理
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if 100 <= pyxel.mouse_x <= 120 and 5 <= pyxel.mouse_y <= 15:
                self.show_shop = not self.show_shop  # ショップ画面の表示切替

        # ゲームクリアボタンのクリック処理
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if all(cat.level >= self.max_level for cat in self.spawnable_catspecies):
                if 100 <= pyxel.mouse_x <= 130 and 110 <= pyxel.mouse_y <= 120:
                    self.state = self.GAMECLEAR  # ゲームクリア画面に移動

        # ショップ画面でのクリック処理
        if self.show_shop:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                for i, cat in enumerate(self.spawnable_catspecies):
                    if (
                        105 <= pyxel.mouse_x <= 120
                        and 18 + i * 10 <= pyxel.mouse_y <= 26 + i * 10
                    ):
                        if cat.level == self.max_level:  # 上限レベルの場合はスキップ
                            continue

                        if self.money >= cat.sell_price[cat.level]:
                            self.money -= cat.sell_price[cat.level]
                            self.spawnable_catspecies[i].level += 1

                            # 作成済みのcatのclicl_priceを更新
                            for ind_cat in self.cats:
                                if ind_cat.name == cat.name:
                                    ind_cat.click_price = cat.click_price[cat.level]

        # 猫種別毎に出現時間を更新
        for cat in self.spawnable_catspecies:
            # print(f"cat: {cat.name}, level: {cat.level}")
            if cat.level == 0:  # 未出現の場合はスキップ
                continue
            cat.spawn_timer -= 1
            if cat.spawn_timer <= 0:
                x = random.randint(0, pyxel.width - 16)
                y = random.randint(0, pyxel.height - 16)
                anim_start_time = random.randint(0, 30)
                self.cats.append(
                    CAT(
                        cat.name,
                        cat.anim0,
                        cat.anim1,
                        cat.click_price[cat.level],
                        x,
                        y,
                        anim_start_time,
                    )
                )
                cat.spawn_timer = cat.spawn_time

        # クリック処理
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.check_click(pyxel.mouse_x, pyxel.mouse_y)

        # テキストエフェクトの更新
        for particle in self.particles:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

    def draw(self):
        # pyxel.cls(6)  # 背景色
        pyxel.bltm(0, 0, 0, 0, 0, 256, 256)  # 背景表示

        if self.state == self.GAMECLEAR:
            pyxel.cls(6)  # 背景
            pyxel.text(20, 30, "Thank you for playing!", 7)

            # 6匹の猫を横一列に表示
            cat_spacing = pyxel.width // 7  # 均等な間隔を計算
            for i, cat in enumerate(self.spawnable_catspecies):
                x = cat_spacing * (i + 1) - 5  # 各猫のx座標
                y = 60  # y座標は固定

                # アニメーション処理
                if (
                    self.animation_frame + i * 5
                ) % 30 < 15:  # 各猫のアニメーションをずらす
                    sheet, sprite_x, sprite_y, w, h, bg = cat.anim0
                else:
                    sheet, sprite_x, sprite_y, w, h, bg = cat.anim1
                pyxel.blt(x, y, sheet, sprite_x, sprite_y, w, h, bg)

            # メイン画面に戻るボタン
            pyxel.rect(25, 90, 36, 10, 8)  # Continueボタンの背景
            pyxel.text(27, 92, "Continue", 7)  # Continueボタンのテキスト

            # リスタートボタン
            pyxel.rect(70, 90, 32, 10, 8)  # Restartボタンの背景
            pyxel.text(72, 92, "Restart", 7)  # Restartボタンのテキスト

            return

        if self.state == self.MAIN:
            for cat in self.cats:
                px = cat.x
                py = cat.y
                if (self.animation_frame + cat.anim_start_time) % 30 < 15:
                    sheet, x, y, w, h, bg = cat.anim0
                    pyxel.blt(px, py, sheet, x, y, w, h, bg)  # 最初の画像
                else:
                    sheet, x, y, w, h, bg = cat.anim1
                    pyxel.blt(px, py, sheet, x, y, w, h, bg)

            pyxel.text(5, 5, f"Money: {self.money}", 7)  # お金の表示

            # テキストエフェクトの描画
            for particle in self.particles:
                pyxel.text(particle.x, particle.y, particle.text, 7)

        # 購入ボタンの描画
        pyxel.rect(100, 5, 20, 10, 8)  # ボタンの背景
        pyxel.text(102, 7, "Shop", 7)  # ボタンのテキスト

        # ゲームクリアボタンの表示
        # すべてのLVがMAXの場合に表示
        if all(cat.level >= self.max_level for cat in self.spawnable_catspecies):
            pyxel.rect(100, 110, 30, 10, 8)  # ボタンの背景
            pyxel.text(102, 112, "Ending", 7)  # ボタンのテキスト

        # ショップ画面の描画
        if self.show_shop:
            pyxel.rect(5, 15, 120, 110, 0)  # ショップの背景
            for i, cat in enumerate(self.spawnable_catspecies):
                # 名前とLVを分けて表示
                pyxel.text(
                    10,
                    20 + i * 10,
                    f"{cat.name}",
                    7,
                )
                pyxel.text(
                    45,  # 固定位置にLVを表示
                    20 + i * 10,
                    "LV:MAX" if cat.level == self.max_level else f"LV:{cat.level}",
                    7,
                )
                if cat.level != self.max_level:  # レベルがMAXの場合はスキップ
                    pyxel.text(
                        65,  # 価格も固定位置に表示
                        20 + i * 10,
                        f"{cat.sell_price[cat.level]} yen",
                        7,
                    )
                    # 購入ボタンを追加
                    pyxel.rect(105, 18 + i * 10, 15, 8, 8)
                    pyxel.text(107, 20 + i * 10, "Buy", 7)


APP()
