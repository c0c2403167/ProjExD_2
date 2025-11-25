import os
import random
import sys
import pygame as pg


WIDTH, HEIGHT = 1100, 650
DELTA = {
    pg.K_UP:   (0, -5),
    pg.K_DOWN:  (0, +5),
    pg.K_LEFT:  (-5, 0),
    pg.K_RIGHT: (+5, 0),
}
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(rct: pg.Rect) -> tuple[bool, bool]:
    """
    引数:こうかとんRectまたは爆弾Rect
    戻り値：判定効果タブル（横方向, 縦方向）
    画面内ならTrue, 画面外ならFalse
    """
    yoko, tate = True, True
    if rct.left < 0 or WIDTH < rct.right:  # 横方向のはみ出しチェック
        yoko = False
    if rct.top < 0 or HEIGHT < rct.bottom:  # 縦方向のはみ出しチェック
        tate = False
    return yoko, tate


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    時間とともに爆弾が拡大・加速するための
    爆弾Surfaceのリストと加速度のリストを作成して返す関数.
    """
    bb_imgs: list[pg.Surface] = []
    for r in range(1, 11):  # 1〜10段階
        bb_img = pg.Surface((20*r, 20*r))
        pg.draw.circle(bb_img, (255, 0, 0), (10*r, 10*r), 10*r)
        bb_img.set_colorkey((0, 0, 0))
        bb_imgs.append(bb_img)
    bb_accs: list[int] = [a for a in range(1, 11)]
    return bb_imgs, bb_accs

def game_over(screen: pg.Surface, bg_img: pg.Surface) -> None:
    # 背景
    screen.blit(bg_img, (0, 0))

    # 半透明の黒で暗くする
    screen.fill((0, 0, 0))
   

    # 泣きこうかとん
    cry_L = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)
    cry_R = pg.transform.flip(cry_L, True, False)

    # Game Over
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


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")    
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200
    bb_img = pg.Surface((20, 20))  # 爆弾用の空のSurface
    pg.draw.circle(bb_img, (255, 0, 0), (10, 10), 10)  # 赤い円を描く
    bb_img.set_colorkey((0, 0, 0))  # 黒色を透明に設定
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)  # 爆弾の初期位置

    bb_imgs, bb_accs = init_bb_imgs()      # 段階ごとの爆弾と加速度リストを取得
    bb_img = bb_imgs[0]                    # 最初は一番小さい爆弾を使う
    bb_rct = bb_img.get_rect(center=bb_rct.center)  # 中心はさっき決めた位置のまま
    
    vx, vy = +5, +5  # 爆弾の速度(横, 縦)
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
            
        if kk_rct.colliderect(bb_rct):  # こうかとんと爆弾が衝突したら
            game_over(screen, bg_img)
            return 
        screen.blit(bg_img, [0, 0]) 

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        if key_lst[pg.K_UP]:
            sum_mv[1] -= 5
        if key_lst[pg.K_DOWN]:
            sum_mv[1] += 5
        if key_lst[pg.K_LEFT]:
            sum_mv[0] -= 5
        if key_lst[pg.K_RIGHT]:
            sum_mv[0] += 5
        for key, mv in DELTA.items():
            if key_lst[key]:
                sum_mv[0] += mv[0] # 横方向の移動量を加算
                sum_mv[1] += mv[1] # 縦方向の移動量を加算
        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):  # 画面外なら
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])  #移動を無かったことにする
            
        screen.blit(kk_img, kk_rct)

        # 時間とともに爆弾が拡大・加速する
        idx = min(tmr // 500, 1)  # 500フレームごとに1段階アップ

        # 爆弾画像を段階に応じて切り替える
        old_center = bb_rct.center         # 位置は維持したいので一旦保存
        bb_img = bb_imgs[idx]
        bb_rct = bb_img.get_rect()         # 新しいサイズのRectを作り直す
        bb_rct.center = old_center

        # 加速度付きの速度を計算
        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]

        # 画面端チェック（向きの反転は基準速度vx,vyに対して行う）
        yoko, tate = check_bound(bb_rct)
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1

        # 反転したかもしれないので、もう一度加速度をかける
        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]

        # 加速された速度で移動
        bb_rct.move_ip(avx, avy)

        # 爆弾を描画
        screen.blit(bb_img, bb_rct)
        # ==== ここまで演習2の処理 ====


        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()