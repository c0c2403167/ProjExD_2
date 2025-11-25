import os
import random
import sys
import pygame as pg


WIDTH, HEIGHT = 1100, 650
DELTA = {
    pg.K_UP:    (0, -5),
    pg.K_DOWN:  (0, +5),
    pg.K_LEFT:  (-5, 0),
    pg.K_RIGHT: (+5, 0),
}

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(rct: pg.Rect) -> tuple[bool, bool]:
    """
    引数 : こうかとんRect または 爆弾Rect
    戻り値 : (横方向が画面内か, 縦方向が画面内か)
    画面内なら True, 画面外なら False
    """
    yoko, tate = True, True
    if rct.left < 0 or WIDTH < rct.right:   # 横方向のはみ出しチェック
        yoko = False
    if rct.top < 0 or HEIGHT < rct.bottom:  # 縦方向のはみ出しチェック
        tate = False
    return yoko, tate


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    時間とともに爆弾が拡大・加速するための
    爆弾Surfaceのリストと加速度のリストを作成して返す.
    """
    bb_imgs: list[pg.Surface] = []
    for r in range(1, 11):  # 1〜10段階
        bb_img = pg.Surface((20*r, 20*r))
        pg.draw.circle(bb_img, (255, 0, 0), (10*r, 10*r), 10*r)
        bb_img.set_colorkey((0, 0, 0))
        bb_imgs.append(bb_img)
    bb_accs: list[int] = [a for a in range(1, 11)]
    return bb_imgs, bb_accs


def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]: 
    """
    こうかとんの向きごとの画像をまとめた辞書を作って返す関数.
    キーは移動量(dx, dy)、値はその向きのこうかとん画像Surface。
    """
    base = pg.image.load("fig/3.png")          # 左向き
    base = pg.transform.rotozoom(base, 0, 0.9)
    right = pg.transform.flip(base, True, False)

    kk_imgs: dict[tuple[int, int], pg.Surface] = {}

    kk_imgs[(0, 0)]   = right                  # 静止
    kk_imgs[(+5, 0)]  = right                  # 右
    kk_imgs[(-5, 0)]  = base                   # 左

    kk_imgs[(0, -5)]  = pg.transform.rotozoom(base, -90, 0.9)   # 上
    kk_imgs[(0, +5)]  = pg.transform.rotozoom(base,  90, 0.9)   # 下

    kk_imgs[(+5, -5)] = pg.transform.rotozoom(right,  45, 0.9)  # 右上
    kk_imgs[(+5, +5)] = pg.transform.rotozoom(right, -45, 0.9)  # 右下
    kk_imgs[(-5, +5)] = pg.transform.rotozoom(base,   45, 0.9)  # 左上
    kk_imgs[(-5, -5)] = pg.transform.rotozoom(base,  -45, 0.9)  # 左下

    return kk_imgs




def game_over(screen: pg.Surface) -> None:
    """
    ゲームオーバー画面を表示する.
    背景を真っ黒にし，左右に泣きこうかとん，中央に 'Game Over' を出す.
    """
    screen.fill((0, 0, 0))

    cry_L = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)
    cry_R = pg.transform.flip(cry_L, True, False)

    font = pg.font.Font(None, 100)
    text = font.render("Game Over", True, (255, 255, 255))
    text_rct = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    margin = 40
    left_rct = cry_L.get_rect()
    right_rct = cry_R.get_rect()
    left_rct.centery = right_rct.centery = text_rct.centery
    left_rct.centerx = text_rct.left - margin
    right_rct.centerx = text_rct.right + margin

    screen.blit(cry_L, left_rct)
    screen.blit(cry_R, right_rct)
    screen.blit(text, text_rct)
    pg.display.update()
    pg.time.wait(5000)


def main() -> None:
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    # こうかとん画像
    kk_imgs = get_kk_imgs()
    kk_img = kk_imgs[(0, 0)]
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    # 爆弾
    bb_imgs, bb_accs = init_bb_imgs()
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)

    vx, vy = +5, +5  # 爆弾の基準速度
    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        # 衝突したらゲームオーバー画面
        if kk_rct.colliderect(bb_rct):
            game_over(screen)
            return

        # 背景
        screen.blit(bg_img, (0, 0))

        # こうかとんの移動＆向き
        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        for key, mv in DELTA.items():
            if key_lst[key]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        kk_img = kk_imgs.get(tuple(sum_mv), kk_imgs[(0, 0)])

        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])
        screen.blit(kk_img, kk_rct)

        # 爆弾の拡大＆加速
        idx = min(tmr // 500, 9)  # 0〜9段階

        old_center = bb_rct.center
        bb_img = bb_imgs[idx]
        bb_rct = bb_img.get_rect()
        bb_rct.center = old_center

        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]

        yoko, tate = check_bound(bb_rct)
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1

        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]

        bb_rct.move_ip(avx, avy)
        screen.blit(bb_img, bb_rct)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
