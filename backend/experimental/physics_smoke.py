import pybullet as p
import pybullet_data
import time

# 1. Подключаемся к симулятору с графическим интерфейсом (GUI)
physicsClient = p.connect(p.GUI)

# 2. Подключаем стандартные 3D-модели PyBullet (земля, роботы и т.д.)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# 3. Включаем реалистичную гравитацию Земли
p.setGravity(0, 0, -9.81)

# 4. Загружаем стандартную плоскость (пол-сетку)
floor_id = p.loadURDF("plane.urdf")

# 5. Загружаем какой-нибудь объект, например, тестовую цифровую коробку (R2D2 или куб)
# Для теста загрузим простую плоскость, чтобы увидеть, что окно открылось
print("Движок PyBullet работает отлично!")

# Держим окно открытым 10 секунд и просчитываем физику
for _ in range(1000):
    p.stepSimulation()
    time.sleep(1./240.) # Стандартный шаг времени для PyBullet

# Отключаемся
p.disconnect()