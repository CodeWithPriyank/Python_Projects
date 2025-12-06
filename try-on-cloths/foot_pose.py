import cv2

# Load right shoe image with alpha (RGBA)
right_shoe = cv2.imread("shoe_render.png", cv2.IMREAD_UNCHANGED)

# Flip horizontally to get left shoe
left_shoe = cv2.flip(right_shoe, 1)

# Save flipped image
cv2.imwrite("shoe_render_left.png", left_shoe)
cv2.imwrite("shoe_render_right.png", right_shoe)

print("✅ Left shoe image saved as 'shoe_render_left.png'")
