import os
import shutil

images_path = 'naive_spider/images'
train_path  = os.path.join(images_path, 'train')
val_path    = os.path.join(images_path, 'val')
test_path   = os.path.join(images_path, 'test')

files = os.listdir(train_path)
print('total: %d' % len(files))

for i, file in enumerate(sorted(files)):
    shutil.move(os.path.join(train_path, file), os.path.join(train_path, '%d.jpg' % (i+1)))

files = os.listdir(val_path)
print('total: %d' % len(files))
for i, file in enumerate(sorted(files)):
    shutil.move(os.path.join(val_path, file), os.path.join(val_path, '%d.jpg' % (i+1)))

files = os.listdir(test_path)
print('total: %d' % len(files))
for i, file in enumerate(sorted(files)):
    shutil.move(os.path.join(test_path, file), os.path.join(test_path, '%d.jpg' % (i+1)))

# files = sorted(files)
# trains = files[:3500]
# vals   = files[3500:4000]
# tests  = files[4000:]


# print('=> move train')
# i = 0;
# for file in trains:
#     shutil.move(os.path.join(images_path, file), os.path.join(train_path, file))
#     i += 1
#     if i % 100 == 0:
#         print(i)

# print('=> move val')
# for file in vals:
#     shutil.move(os.path.join(images_path, file), os.path.join(val_path, file))
#     i += 1
#     if i % 100 == 0:
#         print(i)

# print('=> move test')
# for file in tests:
#     shutil.move(os.path.join(images_path, file), os.path.join(test_path, file))
#     i += 1
#     if i % 100 == 0:
#         print(i)
