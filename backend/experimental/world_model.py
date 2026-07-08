"""
Foresight — Digital Twin (World Model) на базе PyBullet.

Цифровой двойник колесного робота Husky, который проходит
через узкий проём. World Model предсказывает риск столкновения
методом Монте-Карло; движение полностью физическое (колёса).
"""

import math
import random

import pybullet as p
import pybullet_data


# Параметры узкого прохода (метры)
PASSAGE_GAP = 0.65
PASSAGE_Y = 0.0
WALL_HALF_EXTENTS = [0.15, 0.6, 0.75]  # стены только вокруг проёма (Y ≈ 0), не до точки спавна

# Параметры привода Husky
WHEEL_MAX_FORCE = 1000.0
MC_TIMESTEPS = 60


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class DigitalTwin:
    """Цифровой двойник Husky и окружения (пол + узкий проход)."""

    def __init__(self, use_gui: bool = True):
        """
        Инициализация симуляции PyBullet.

        Args:
            use_gui: True — окно GUI для демонстрации; False — headless (DIRECT).
        """
        mode = p.GUI if use_gui else p.DIRECT
        self.client = p.connect(mode)

        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)

        if use_gui:
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
            p.resetDebugVisualizerCamera(
                cameraDistance=5.0,
                cameraYaw=90,
                cameraPitch=-40,
                cameraTargetPosition=[0, 0, 0.5],
            )

        self.floor = p.loadURDF("plane.urdf")

        # Clearpath Husky — колесный робот на полу, развёрнут лицом к проходу (+Y)
        spawn_orn = p.getQuaternionFromEuler([0.0, 0.0, math.pi / 2.0])
        self.robot_id = p.loadURDF(
            "husky/husky.urdf",
            basePosition=[0, -1.8, 0.0],
            baseOrientation=spawn_orn,
            useFixedBase=False,
        )

        # Индексы ведущих колёс (в URDF Husky: front/rear left/right wheel)
        self.wheel_joints = self._find_wheel_joints()

        # Текущая команда скорости (для Монте-Карло и Safeguard)
        self.current_linear_vel = 0.0
        self.current_angular_vel = 0.0

        self.obstacles: list[int] = []
        self._build_passage()

        # Дать роботу «осесть» на пол после загрузки URDF
        for _ in range(120):
            p.stepSimulation()

        pos, _ = p.getBasePositionAndOrientation(self.robot_id)
        self.robot_z = pos[2]

    def _find_wheel_joints(self) -> list[int]:
        """Находит суставы колёс по ключевому слову 'wheel' в названии."""
        wheel_joints: list[int] = []
        num_joints = p.getNumJoints(self.robot_id)

        for joint_index in range(num_joints):
            joint_name = p.getJointInfo(self.robot_id, joint_index)[1].decode("utf-8")
            if "wheel" in joint_name.lower():
                wheel_joints.append(joint_index)

        if not wheel_joints:
            raise RuntimeError("Не найдены суставы колёс в URDF Husky.")

        return wheel_joints

    def _build_passage(self) -> None:
        """Создаёт дверной проём из двух статичных стен."""
        wall_half_x = WALL_HALF_EXTENTS[0]
        gap_half = PASSAGE_GAP / 2.0
        wall_center_x = gap_half + wall_half_x

        left_color = [0.75, 0.2, 0.2, 0.9]
        right_color = [0.2, 0.35, 0.85, 0.9]

        self.obstacles.append(
            self._create_wall([-wall_center_x, PASSAGE_Y, WALL_HALF_EXTENTS[2]], left_color)
        )
        self.obstacles.append(
            self._create_wall([wall_center_x, PASSAGE_Y, WALL_HALF_EXTENTS[2]], right_color)
        )

    def _create_wall(self, position: list[float], rgba: list[float]) -> int:
        """Создаёт одну статичную стену-препятствие."""
        visual = p.createVisualShape(
            shapeType=p.GEOM_BOX,
            halfExtents=WALL_HALF_EXTENTS,
            rgbaColor=rgba,
        )
        collision = p.createCollisionShape(
            shapeType=p.GEOM_BOX,
            halfExtents=WALL_HALF_EXTENTS,
        )
        return p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=collision,
            baseVisualShapeIndex=visual,
            basePosition=position,
        )

    def set_velocity(self, linear_vel: float, angular_vel: float) -> None:
        """
        Задаёт скорость Husky через вращение колёс (дифференциальный привод).

        Левые колёса: linear_vel - angular_vel
        Правые колёса: linear_vel + angular_vel

        Args:
            linear_vel:  Линейная скорость (рад/с на оси колеса).
            angular_vel: Угловая скорость поворота (рад/с, дифференциал).
        """
        self.current_linear_vel = linear_vel
        self.current_angular_vel = angular_vel

        left_speed = linear_vel - angular_vel
        right_speed = linear_vel + angular_vel

        for joint_index in self.wheel_joints:
            joint_name = p.getJointInfo(self.robot_id, joint_index)[1].decode("utf-8").lower()

            if "left" in joint_name:
                target = left_speed
            elif "right" in joint_name:
                target = right_speed
            else:
                target = linear_vel

            p.setJointMotorControl2(
                bodyUniqueId=self.robot_id,
                jointIndex=joint_index,
                controlMode=p.VELOCITY_CONTROL,
                targetVelocity=target,
                force=WHEEL_MAX_FORCE,
            )

    def update_robot_pose(self, x: float, y: float, yaw: float) -> None:
        """
        Обновляет позу Husky по данным Limelight / YOLO (телепорт + сброс скоростей).

        После установки позы колёса останавливаются, чтобы физика не «боролась»
        с координатами от камеры.
        """
        orientation = p.getQuaternionFromEuler([0.0, 0.0, yaw])
        p.resetBasePositionAndOrientation(self.robot_id, [x, y, self.robot_z], orientation)
        p.resetBaseVelocity(
            self.robot_id,
            linearVelocity=[0.0, 0.0, 0.0],
            angularVelocity=[0.0, 0.0, 0.0],
        )
        self.current_linear_vel = 0.0
        self.current_angular_vel = 0.0
        for joint_index in self.wheel_joints:
            p.setJointMotorControl2(
                self.robot_id,
                joint_index,
                p.VELOCITY_CONTROL,
                targetVelocity=0.0,
                force=WHEEL_MAX_FORCE,
            )

    def update_motion_intent(self, linear_vel: float, angular_vel: float) -> None:
        """
        Сохраняет «намерение» движения для Монте-Карло без вращения колёс.

        Используется, когда поза приходит от Limelight, а прогноз риска
        должен учитывать текущий вектор движения.
        """
        self.current_linear_vel = linear_vel
        self.current_angular_vel = angular_vel

    def get_robot_pose(self) -> tuple[float, float, float]:
        """Возвращает текущую позу робота: x, y, yaw (радианы)."""
        pos, orn = p.getBasePositionAndOrientation(self.robot_id)
        _, _, yaw = p.getEulerFromQuaternion(orn)
        return pos[0], pos[1], yaw

    def _check_robot_wall_collision(self) -> bool:
        """Проверяет контакт робота с любой из стен прохода."""
        for obstacle_id in self.obstacles:
            contacts = p.getContactPoints(bodyA=self.robot_id, bodyB=obstacle_id)
            if contacts:
                return True
        return False

    def predict_collision_risk(self, num_simulations: int = 15) -> float:
        """
        Монте-Карло оценка риска столкновения со стенами прохода.

        Снимает слепок мира, симулирует будущее с погрешностями скорости
        на MC_TIMESTEPS шагов и проверяет контакты через getContactPoints.
        """
        collisions = 0
        gui_mode = p.getConnectionInfo()["connectionMethod"] == p.GUI

        if gui_mode:
            p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 0)

        state_id = p.saveState()

        try:
            base_linear = self.current_linear_vel
            base_angular = self.current_angular_vel

            for _ in range(num_simulations):
                p.restoreState(state_id)

                # Случайные погрешности команды скорости (шум навигации / привода)
                sim_linear = base_linear + random.uniform(-0.3, 0.3)
                sim_angular = base_angular + random.uniform(-0.08, 0.08)

                for _ in range(MC_TIMESTEPS):
                    self.set_velocity(sim_linear, sim_angular)
                    p.stepSimulation()

                if self._check_robot_wall_collision():
                    collisions += 1

        finally:
            p.restoreState(state_id)
            p.removeState(state_id)
            # Восстанавливаем актуальную команду скорости после прогона
            self.set_velocity(self.current_linear_vel, self.current_angular_vel)
            if gui_mode:
                p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1)

        return (collisions / num_simulations) * 100.0

    def _detect_falling_objects(self) -> bool:
        """
        Заглушка детектора падающих объектов в симуляции.

        TODO: подключить YOLO / семантический контур (LocateAnything-3B).
        Сейчас: проверяем резкое падение по оси Z у динамических тел.
        """
        for body_id in range(p.getNumBodies()):
            if body_id in (self.floor, self.robot_id, *self.obstacles):
                continue
            pos, _ = p.getBasePositionAndOrientation(body_id)
            lin_vel, _ = p.getBaseVelocity(body_id)
            if pos[2] < 0.3 and lin_vel[2] < -0.5:
                return True
        return False

    def step_physics(self, steps: int = 10, dt: float = 1.0 / 240.0) -> None:
        """Прокручивает физику на несколько шагов (движение колёс + GUI)."""
        import time

        gui_mode = p.getConnectionInfo()["connectionMethod"] == p.GUI
        for _ in range(steps):
            p.stepSimulation()
            if gui_mode:
                time.sleep(dt)

    def disconnect(self) -> None:
        """Корректное отключение от PyBullet."""
        if p.isConnected():
            p.disconnect()


# ---------------------------------------------------------------------------
# «Мозг» — слой безопасности World Model
# ---------------------------------------------------------------------------

class SafetyBrain:
    """
    Командир в экстренных ситуациях: фильтрует желаемые скорости от камеры.

    Камера (Limelight) — ведущая в штатном режиме.
    Мозг переопределяет команды при:
      - AprilTag ближе STOP_DISTANCE_M (pose z) или ta > TA_APRILTAG_EMERGENCY
      - высоком риске столкновения со стеной (Монте-Карло)
      - событиях: падающие объекты, взрывы (заглушки / расширяемые хуки)
    """

    RISK_CRITICAL = 75.0
    RISK_WARNING = 30.0

    # AprilTag: жёсткая зона остановки по дистанции (метры)
    STOP_DISTANCE_M = 0.4
    CAUTION_DISTANCE_M = 1.0

    # Fallback, если Pose (z) недоступен — ta для AprilTag (меньше, чем для цвета)
    TA_APRILTAG_EMERGENCY = 8.0

    def __init__(self, twin: DigitalTwin):
        self.twin = twin
        self.last_risk = 0.0
        self.active_events: list[str] = []
        self.override_active = False

        # Флаг внешнего события «взрыв» (можно выставить из другого контура)
        self.explosion_detected = False

    def _check_explosion_event(self) -> bool:
        """Заглушка детектора взрыва / резкого события среды."""
        return self.explosion_detected

    def evaluate(
        self,
        target_linear: float,
        target_angular: float,
        ta: float = 0.0,
        distance_z: float | None = None,
        tag_valid: bool = True,
    ) -> dict:
        """
        Фильтр команд: desired velocity → final velocity.

        Args:
            target_linear:  Желаемая линейная скорость от виртуального джойстика.
            target_angular: Желаемая угловая скорость от виртуального джойстика.
            ta:             Target Area (%) — fallback, если Pose недоступен.
            distance_z:     Дистанция до AprilTag по Pose (м).
            tag_valid:      False — маркер потерян (вне кадра).
        """
        self.active_events = []
        self.override_active = False

        if not tag_valid:
            self.active_events.append("tag_lost")
            return self._result(
                0.0, 0.0,
                approved=False,
                status="TAG_LOST",
                reason="AprilTag потерян — плавная остановка",
            )

        # --- Приоритет 1: AprilTag слишком близко (Pose z точнее ta) ---
        if distance_z is not None and distance_z < self.STOP_DISTANCE_M:
            self.active_events.append("apriltag_close")
            self.override_active = True
            return self._result(
                0.0, 0.0,
                approved=False,
                status="EMERGENCY_APRILTAG",
                reason=f"AprilTag z={distance_z:.2f} м < {self.STOP_DISTANCE_M} м",
            )

        if distance_z is None and ta > self.TA_APRILTAG_EMERGENCY:
            self.active_events.append("ta_proximity")
            self.override_active = True
            return self._result(
                0.0, 0.0,
                approved=False,
                status="EMERGENCY_TA",
                reason=f"ta={ta:.1f}% > {self.TA_APRILTAG_EMERGENCY}% (fallback)",
            )

        # Зона предосторожности: снижение скорости при z < 1.0 м
        if distance_z is not None and distance_z < self.CAUTION_DISTANCE_M:
            span = self.CAUTION_DISTANCE_M - self.STOP_DISTANCE_M
            scale = clamp((distance_z - self.STOP_DISTANCE_M) / span, 0.15, 1.0)
            self.active_events.append("apriltag_caution")
            target_linear *= scale

        # --- Приоритет 2: взрыв / резкое событие ---
        if self._check_explosion_event():
            self.active_events.append("explosion")
            self.override_active = True
            self.explosion_detected = False
            return self._result(
                0.0, 0.0,
                approved=False,
                status="EMERGENCY_EXPLOSION",
                reason="обнаружено событие взрыва",
            )

        # --- Приоритет 3: падающие объекты ---
        if self.twin._detect_falling_objects():
            self.active_events.append("falling_object")
            self.override_active = True
            return self._result(
                0.0, 0.0,
                approved=False,
                status="EMERGENCY_FALLING",
                reason="падающий объект в зоне",
            )

        # --- Прогноз столкновения (Монте-Карло) по ЖЕЛАЕМОЙ скорости камеры ---
        self.twin.update_motion_intent(target_linear, target_angular)
        self.last_risk = self.twin.predict_collision_risk(num_simulations=15)

        if self.last_risk > self.RISK_CRITICAL:
            self.active_events.append("wall_risk")
            self.override_active = True
            return self._result(
                0.0, 0.0,
                approved=False,
                status="EMERGENCY_WALL",
                reason=f"риск столкновения {self.last_risk:.1f}%",
            )

        # --- Предупреждение: снижаем скорость, но не перехватываем полностью ---
        if self.last_risk >= self.RISK_WARNING:
            self.active_events.append("wall_warning")
            scale = 1.0 - 0.5 * (
                (self.last_risk - self.RISK_WARNING)
                / (self.RISK_CRITICAL - self.RISK_WARNING)
            )
            scale = clamp(scale, 0.3, 1.0)
            return self._result(
                target_linear * scale,
                target_angular,
                approved=True,
                status="CAUTION",
                reason=f"риск {self.last_risk:.1f}% — снижение скорости",
            )

        # --- Штатный режим: камера ведущая, Мозг одобряет без изменений ---
        return self._result(
            target_linear,
            target_angular,
            approved=True,
            status="NORMAL",
            reason="опасностей не обнаружено",
        )

    def _result(
        self,
        final_linear: float,
        final_angular: float,
        approved: bool,
        status: str,
        reason: str,
    ) -> dict:
        return {
            "final_linear": final_linear,
            "final_angular": final_angular,
            "approved": approved,
            "override": self.override_active,
            "risk": self.last_risk,
            "events": list(self.active_events),
            "status": status,
            "reason": reason,
        }


if __name__ == "__main__":
    twin = DigitalTwin(use_gui=True)
    twin.set_velocity(1.0, 0.1)

    print("Запуск предсказания риска столкновения...")
    risk = twin.predict_collision_risk()
    print(f"Риск столкновения: {risk:.1f}%")

    twin.disconnect()
