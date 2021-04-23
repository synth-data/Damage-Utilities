from imageutils import write_mask

AMOUNT = 1000
RESOLUTION = 128
SPLASH = False

for render_id in range(1, AMOUNT + 1):
    write_mask('../batch_output/' + str(render_id) + '.csv', '../batch_masks/' + str(render_id) + '.png', RESOLUTION, splash=SPLASH)
