
import sys, pygame
import math
import random
import numpy
from enum import Enum

# 5 pixels ~ 1m

# EDITABLE
PACKET_DELAY = 1 # Minimum is 1 frame
PACKET_LOSS_CHANCE = 0
CAR_AMOUNT = 20
ROUTER_RANGE = 40

# Initializing
pygame.init()

size = screen_width, screen_height = 800, 800
screen = pygame.display.set_mode(size)

# Loads the car as a texture
car_texture = pygame.image.load("car.jpg")
car_texture = pygame.transform.scale(car_texture, (10, 10))

SIM_TICK = 0

def tuple_distance(pos_1, pos_2) -> float:
    return point_distance(pos_1[0], pos_1[1], pos_2[0], pos_2[1])

def point_distance(p1_x, p1_y, p2_x, p2_y) -> float:
    return math.sqrt( math.pow(p1_x - p2_x, 2) + math.pow(p1_y - p2_y, 2))

# Points are all integers on a 2D plane
gened_points = []

# The car we have selected
selected_car = None


def render_gened_points(screen):
    for point in gened_points:
        pygame.draw.circle(screen, (0, 255, 0), point, 2)


class RoadManager:
    def __init__(self):
        self.roads = []

    def reset(self):
        self.roads = []

    def update_roads(self):
        for road in self.roads:
            road.tick()

    def get_roads(self):
        return self.roads

    def add_road(self, road):
        self.roads.append(road)

    def render_roads(self, screen):
        global selected_car

        if selected_car == None:
            for road in self.roads:
                road.render(screen)
        else:
            router = selected_car.router
            router.render_roads(screen)

    def get_roads_with_start_position(self, pos):
        roads_at = []

        for road in self.roads:
            distance = tuple_distance(pos, road.start_position)
            if distance < 2:
                roads_at.append(road)

        return roads_at

    def get_roads_with_end_position(self, pos):
        roads_at = []

        for road in self.roads:
            distance = tuple_distance(pos, road.end_position)
            if distance < 2:
                roads_at.append(road)

        return roads_at
    
    def get_random_road(self):
        if len(self.roads) == 0:
            return None
        
        index = int(random.uniform(0, len(self.roads)))
        return self.roads[index]

    # Generates a map
    def generate_map(self):
        global screen_width, screen_height, gened_points, road_manager

        # Generate a bunch of points
        points = Generator.get_spaced_points(100, 5, screen_width - 100, screen_height - 100)
        # Remove points that were too close
        for point in points:
            for other_point in points:
                if point == other_point:
                    continue
                else:
                    distance = tuple_distance(point, other_point)
                    if distance < 50:
                        points.remove(other_point)

        gened_points = points.copy()
        
        for point in points:
            point[0] += 50
            point[1] += 50

        
        # Generates a few traffic lights
        all_light_points = []
        LIGHT_MAX = 5
        LIGHT_AMOUNT = int(random.uniform(0, LIGHT_MAX) + 3)
        for index in range(LIGHT_AMOUNT):
            point = points[index]
            roads, light_points = Generator.generate_light_intersection(point)
            points.remove(point)

            for road in roads:
                road_manager.add_road(road)

            for light_point in light_points:
                all_light_points.append(light_point)

            # pass

        points_clone = points.copy()
        # Creates a road to the traffic lights
        for light_point in all_light_points:
            points_clone.sort(key = lambda clone_point:tuple_distance(light_point, clone_point))

            if len(points_clone) == 0:
                continue


            start_point = light_point
            end_point = points_clone[0]
            
            new_road = Road(start_point, end_point)

            road_manager.add_road(new_road)
            pass


        points_clone = points.copy()
        iterations = 0
        
        for point in points:
            iterations += 1

            points_clone.sort(key = lambda clone_point:tuple_distance(point, clone_point))
            points_clone.remove(point)

            if len(points_clone) == 0:
                continue

            start_point = point
            end_point = points_clone[0]
            
            new_road = Road(start_point, end_point)

            road_manager.add_road(new_road)

        # Joins the roads together
        all_roads = road_manager.get_roads()

        for road in all_roads:
            start_point = road.start_position
            end_point = road.end_position
            
            roads_at_end = road_manager.get_roads_with_start_position(end_point)
            roads_at_start = road_manager.get_roads_with_end_position(start_point)

            roads_at_end_2 = road_manager.get_roads_with_start_position(start_point)
            roads_at_start_2 = road_manager.get_roads_with_end_position(end_point)

            for start_road in roads_at_start:
                if start_road.tag == road.tag:
                    continue
                start_road.add_end_link(road, 0)

            for end_road in roads_at_end:
                if end_road.tag == road.tag:
                    continue
                road.add_end_link(end_road, 0)

            for match_end_road in roads_at_start_2:
                if match_end_road.tag == road.tag:
                    continue
                match_end_road.add_inverse_link(road, False)
            
            for match_start_road in roads_at_end_2:
                if match_start_road.tag == road.tag:
                    continue
                match_start_road.add_inverse_link(road, True)



# Stores all the roads
road_manager = RoadManager()



TAG_GEN = 1
class Road:
    ROAD_WIDTH = 10
    SPEED_LIMIT = 1

    def __init__(self, start_pos, end_pos):
        global TAG_GEN
        # Generates a new tag for this road
        TAG_GEN += 1
        self.tag = TAG_GEN
        
        # Links that come into this road
        self.incoming_links = []

        self.end_links = [] # Links at the end of the road
        self.side_links = [] # Links that leave the road
        self.inverse_links = [] # Links that connect start -> start & end -> end

        self.start_position = start_pos
        self.end_position = end_pos

        self.length = point_distance(self.start_position[0], self.start_position[1], self.end_position[0], self.end_position[1])

    def tick(self):
        pass

    # Gets the distance 
    def get_distance_on_incoming_link(self, ROAD_TAG) -> float:
        for link, distance  in self.incoming_links:
            if link.tag == ROAD_TAG:
                return distance
            
        return 0

    # Incoming link
    def add_incoming_link(self, link, distance_down_road):
        self.incoming_links.append((link, distance_down_road))


    def add_inverse_link(self, link, start_to_start):
        self.inverse_links.append((link, start_to_start))
        link.inverse_links.append((self, start_to_start))

    def get_start_inverse_links(self) -> list:
        start_inverse_links = []

        for link, start_to_start in self.inverse_links:
            if start_to_start == True:
                start_inverse_links.append(link)
        
        return start_inverse_links

    def get_end_inverse_links(self) -> list:
        end_inverse_links = []

        for link, start_to_start in self.inverse_links:
            if start_to_start == False:
                end_inverse_links.append(link)
        
        return end_inverse_links

    # End link
    def add_end_link(self, link, distance_on_end_link):
        self.end_links.append((link, distance_on_end_link))
        link.add_incoming_link(self, distance_on_end_link)

    # Gets the direction vector
    def get_direction_vector(self) -> tuple[float, float]:
        vector = [0, 0]
        vector[0] = (self.end_position[0] - self.start_position[0]) / self.get_length()
        vector[1] = (self.end_position[1] - self.start_position[1]) / self.get_length()
        return vector

    # Side link
    def add_side_link(self, link, distance_on_side_link):
        self.side_links.append((link, distance_on_side_link))
        link.add_incoming_link(self, distance_on_side_link)

    def get_start_links(self) -> list[tuple[object, float, bool]]:
        start_links = []

        for (link, distance) in self.incoming_links:
            if distance == 0:
                start_links.append((link, link.get_length()))

        return start_links

    # Gets the end link...
    def get_end_links(self) -> list[tuple[object, float, bool]]:
        return self.end_links

    def get_speed_limit(self) -> float:
        return self.SPEED_LIMIT

    def get_length(self) -> float:
        return self.length
    
    # Percentage Distance
    def get_percentage_distance(self, percentage) -> float:
        t_val = min(1, percentage)
        t_val = max(0, t_val)

        return t_val * self.get_length()

    def get_percentage_pos(self, percentage) -> tuple[int, int]:
        t_val = min(1, percentage)
        t_val = max(0, t_val)
        
        x_val = int(t_val * (self.end_position[0] - self.start_position[0])) + self.start_position[0]
        y_val = int(t_val * (self.end_position[1] - self.start_position[1])) + self.start_position[1]

        return (x_val, y_val)

    def convert_position_to_percentage(self, road_position):
        return float(road_position) / self.length

    def get_integer_pos(self, road_position) -> tuple[int, int]:
        road_position = min(road_position, self.length)
        road_position = max(road_position, 0)

        t_val = self.convert_position_to_percentage(road_position)
        return self.get_percentage_pos(t_val)
    
    def render(self, to_render):
        pygame.draw.line(to_render, (128, 128, 128), self.start_position, self.end_position, width = self.ROAD_WIDTH)

class LightColor(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2

class RedLightLink(Road):
    LIGHT_SWITCH_TIMER = 300
    LIGHT_YELLOW_TIMER = 120
    
    def __init__(self, start_pos, end_pos, start_state):
        super().__init__(start_pos, end_pos)
        self.light_color = start_state

    def tick(self):
        global SIM_TICK

        if (SIM_TICK + self.LIGHT_YELLOW_TIMER) % self.LIGHT_SWITCH_TIMER == 0:
            if self.light_color == LightColor.GREEN:
                self.light_color = LightColor.YELLOW

        if SIM_TICK % self.LIGHT_SWITCH_TIMER == 0:
            if self.light_color == LightColor.RED:
                self.light_color = LightColor.GREEN
            elif self.light_color == LightColor.YELLOW:
                self.light_color = LightColor.RED

    def get_speed_limit(self) -> float:
        if self.light_color == LightColor.GREEN:
            return super().get_speed_limit()
        if self.light_color == LightColor.YELLOW:
            return super().get_speed_limit()
        if self.light_color == LightColor.RED:
            return 0
    
    def render(self, to_render):
        color = [0, 0, 0]
        if self.light_color == LightColor.GREEN:
            color[1] = 255
        if self.light_color == LightColor.YELLOW:
            color[0] = 255
            color[1] = 255
        if self.light_color == LightColor.RED:
            color[0] = 255

        pygame.draw.line(to_render, color, self.start_position, self.end_position, width = self.ROAD_WIDTH)

class CarManager:
    def __init__(self):
        self.cars = []

    def reset(self):
        self.cars = []

    def get_cars(self) -> list:
        return self.cars

    def get_cars_on_road(self, ROAD_TAG) -> list:
        cars_on_road = []

        for car in self.cars:
            car.current_road.tag == ROAD_TAG

        return cars_on_road

    def get_cars_in_range(self, source_car) -> list:
        source_pos = source_car.get_render_position()

        close_cars = []
        for car in self.cars:
            car_pos = car.get_render_position()
            distance = tuple_distance(source_pos, car_pos)

            if distance < source_car.get_connection_range():
                close_cars.append(car)

        return close_cars

    def spawn_cars(self, amount):
        global road_manager

        for _ in range(amount):
            road = road_manager.get_random_road()

            self.add_car(Car(road))

    def add_car(self, car):
        self.cars.append(car)

    # Gets the closest car to the specified point
    def get_closest_car(self, pos):
        if len(self.cars) == 0: 
            return None
        
        closest = None
        closest_dist = None

        for car in self.cars:
            distance = tuple_distance(pos, car.get_render_position())

            if closest == None or distance < closest_dist:
                closest_dist = distance
                closest = car

        return closest

    # Ticks the cars forward a game step
    def drive_cars(self):
        for car in self.cars:
            car.drive()

    # Renders the cars to the screen
    def render_cars(self, screen):
        for car in self.cars:
            car.render(screen)

    def is_car_infront(self, car_tag, current_pos, direction_vector) -> bool:
        global screen

        goal_pos = [0, 0]
        goal_pos[0] = current_pos[0] + (15 * direction_vector[0])
        goal_pos[1] = current_pos[1] + (15 * direction_vector[1])

        pygame.draw.circle(screen, (0, 255, 0), goal_pos, 6)

        for car in self.cars:
            car_pos = car.get_render_position()
            car_direction = car.get_direction_vector()

            dot_product = numpy.dot(direction_vector, car_direction)

            distance = point_distance(car_pos[0], car_pos[1], goal_pos[0], goal_pos[1])

            # Add a direction check to this
            if distance < 10 and car_tag != car.tag and dot_product > 0.4:
                return True

        return False


class Router:
    def __init__(self, car):
        global PACKET_DELAY, PACKET_LOSS_CHANCE, ROUTER_RANGE
        self.car = car

        self.PACKET_DELAY = PACKET_DELAY
        self.PACKET_LOSS_CHANCE = PACKET_LOSS_CHANCE
        self.ROUTER_RANGE = ROUTER_RANGE

        self.traveled_roads = [] # Theses are roads we have been on
        self.known_roads = [] # Roads we have been told about

        self.previous_neighbours = []
        for _ in range(self.PACKET_DELAY):
            self.previous_neighbours.append([])

    def get_traveled_roads(self) -> list[Road]:
        return self.traveled_roads

    def get_pos(self) -> list[int, int]:
        car_pos = self.car.get_render_position()
        
        car_pos[0] += 5
        car_pos[1] += 5

        return car_pos
    
    def tick(self):
        global car_manager
        current_road = self.car.current_road

        if not(current_road in self.traveled_roads):
            self.traveled_roads.append(current_road)

        cars_in_range = car_manager.get_cars_in_range(self.car)

        # 
        self.previous_neighbours.pop(0)
        self.previous_neighbours.append(cars_in_range)

        for car in cars_in_range:
            if car.tag == self.car.tag:
                continue

            valid = True

            for previous in self.previous_neighbours:
                if not(car in previous):
                    valid = False
                    break

            # Packet loss might want to work differently
            if valid: 
                drop_packet = random.uniform(0, 1)
                if drop_packet > self.PACKET_LOSS_CHANCE:
                    for road in car.router.traveled_roads:
                        if not(road in self.traveled_roads):
                            self.traveled_roads.append(road)
                else:
                    # Drops the car from one of the previous neighbours at random
                    # Partially resets the packet delay
                    index_to_drop = int(random.uniform(0, len(self.previous_neighbours)))
                    previous_neighbour = self.previous_neighbours[index_to_drop]
                    previous_neighbour.remove(car)

    
    def render(self, screen):
        self.render_range(screen)

    def render_roads(self, screen):
        for road in self.traveled_roads:
            road.render(screen)

    def render_range(self, screen):
        # Adjusts the car_pos to accurately render the circle
        car_pos = self.get_pos()

        pygame.draw.circle(screen, (255, 0, 0), car_pos, self.ROUTER_RANGE, width = 3)
        pass


class Car:
    DISTANCE_TO_SWITCH_ROADS = 5
    SWITCH_ROAD_CHANCE = 0.05

    TURNAROUND_CHANCE = 0.0001

    def __init__(self, road):
        global TAG_GEN
        TAG_GEN += 1
        self.tag = TAG_GEN
        self.current_road = road
        self.distance_on_road = random.uniform(0, road.get_length())
        self.router = Router(self)

        self.blocked_timer = 0

        # Goes backwards on track
        self.reverse = False

    def respawn(self):
        global road_manager

        random_road = road_manager.get_random_road()
        self.current_road = random_road
        self.distance_on_road = 0
        self.blocked_timer = 0
        self.reverse = False

    def get_direction_vector(self) -> list[float, float]:
        vector = self.current_road.get_direction_vector() 

        if self.reverse:
            vector[0] = -vector[0]
            vector[1] = -vector[1]

        return vector
    
    def get_connection_range(self) -> float:
        return self.router.ROUTER_RANGE

    def get_render_position(self) -> list[int, int]:
        if self.current_road is None:
            return (0, 0)
        road_pos = self.current_road.get_integer_pos(self.distance_on_road)
        return [road_pos[0] - 5, road_pos[1] - 5]
    
    def switch_link(self, link, distance):
        self.current_road = link
        self.distance_on_road = distance

    def drive(self):
        global car_manager

        self.router.tick()

        # Turns around
        turnaround_chance = random.uniform(0, 1)
        if turnaround_chance < self.TURNAROUND_CHANCE:
            self.reverse = not(self.reverse)

        # Ensures it is not hitting another car
        road_pos = self.current_road.get_integer_pos(self.distance_on_road)
        direction_vector = self.get_direction_vector()

        car_infront = car_manager.is_car_infront(self.tag, road_pos, direction_vector)

        if not(car_infront):
            if self.reverse:
                self.distance_on_road -= self.current_road.get_speed_limit()
                self.distance_on_road = max(self.distance_on_road, 0)
            else:
                self.distance_on_road += self.current_road.get_speed_limit()
                self.distance_on_road = min(self.distance_on_road, self.current_road.get_length())

        if car_infront:
            self.blocked_timer += 1

            if self.blocked_timer > 300:
                self.respawn()
        else:
            self.blocked_timer = 0

        # At the end of a current road, switches roads
                    
        # Forwards
        if self.distance_on_road == self.current_road.get_length() and self.reverse == False:
            end_roads = self.current_road.get_end_links()
            inverse_roads = self.current_road.get_end_inverse_links()

            use_normal_links = False
            if len(inverse_roads) != 0 and len(end_roads) != 0:
                picked_links = int(random.uniform(0, 2))
                use_normal_links = (picked_links == 0)
            elif len(end_roads) != 0:
                use_normal_links = True

            if len(end_roads) != 0 and use_normal_links:
                rand_index = int(random.uniform(0, len(end_roads)))
                distance = end_roads[rand_index][0].get_distance_on_incoming_link(self.current_road.tag)
                self.switch_link(end_roads[rand_index][0], distance)
            elif len(inverse_roads) != 0 and use_normal_links == False:
                rand_index = int(random.uniform(0, len(inverse_roads)))
                distance = inverse_roads[rand_index].get_length()
                self.reverse = True
                self.switch_link(inverse_roads[rand_index], distance)
            else:
                self.reverse = not(self.reverse)

        # Backwards
        if self.distance_on_road == 0 and self.reverse == True:
            end_roads = self.current_road.get_start_links()
            inverse_roads = self.current_road.get_start_inverse_links()

            use_normal_links = False
            if len(inverse_roads) != 0 and len(end_roads) != 0:
                picked_links = int(random.uniform(0, 2))
                use_normal_links = (picked_links == 0)
            elif len(end_roads) != 0:
                use_normal_links = True

            if len(end_roads) != 0 and use_normal_links == True:
                rand_index = int(random.uniform(0, len(end_roads)))
                road = end_roads[rand_index][0]
                distance = end_roads[rand_index][1]
                self.switch_link(road, distance)
            elif len(inverse_roads) != 0 and use_normal_links == False:
                rand_index = int(random.uniform(0, len(inverse_roads)))
                self.reverse = False
                self.switch_link(inverse_roads[rand_index], 0)
            else:
                self.reverse = not(self.reverse)


    def render(self, screen):
        self.router.render(screen)

        car_pos = self.get_render_position()
        screen.blit(car_texture, car_pos)

car_manager = CarManager()

class Generator():
    def get_random_point(width, height) -> list[int, int]:
        x_val = int(random.uniform(0, width))
        y_val = int(random.uniform(0, height))

        return [x_val, y_val]
    
    def get_spaced_points(amount, spacing, width, height) -> list[list[int, int]]:
        spaced = False
        points = []

        while not(spaced):
            points = []
            for _ in range(amount):
                points.append(Generator.get_random_point(width, height))

            spaced = True
            for i in range(len(points)):
                if spaced == True:
                    for j in range(len(points)):
                        if i == j:
                            continue
                        distance = tuple_distance(points[i], points[j])
                        if distance < spacing:
                            spaced = False
                            break

        return points

    def generate_light_intersection(center_pos) -> tuple[list[Road], list]:
        global screen_width, screen_height
        # Forces the center pos to be 100 px from the edge
        center_pos[0] = max(min(center_pos[0], screen_width), 50)
        center_pos[1] = max(min(center_pos[1], screen_height), 50)

        LIGHT_LENGTH = 20

        roads = []
        points = []

        # Horizontal Light
        start_pos = [0, 0]
        end_pos = [0, 0]
        start_pos = [0, center_pos[1]]
        start_pos[0] = center_pos[0] - LIGHT_LENGTH
        end_pos = [0, center_pos[1]]
        end_pos[0] = center_pos[0] + LIGHT_LENGTH
        roads.append(RedLightLink(start_pos, end_pos, LightColor.RED))

        # Horizontal Light roads
        start_pos = [0, 0]
        end_pos = [0, 0]
        start_pos = [0, center_pos[1]]
        start_pos[0] = center_pos[0] + LIGHT_LENGTH
        end_pos[0] = center_pos[0] + 50 + random.uniform(0, 50)
        end_pos[1] = center_pos[1] + random.uniform(0, 100) - 50
        points.append([end_pos[0], end_pos[1]])
        roads.append(Road(start_pos, end_pos))
        roads[0].add_end_link(roads[1], 0)
        
        start_pos = [0, 0]
        end_pos = [0, 0]
        start_pos[0] = center_pos[0] - 50 - random.uniform(0, 50)
        start_pos[1] = center_pos[1] + random.uniform(0, 100) - 50
        end_pos[0] = center_pos[0] - LIGHT_LENGTH
        end_pos[1] = center_pos[1]
        points.append([start_pos[0], start_pos[1]])
        roads.append(Road(start_pos, end_pos))
        roads[2].add_end_link(roads[0], 0)

        # Vertical
        start_pos = [0, 0]
        end_pos = [0, 0]
        start_pos = [center_pos[0], 0]
        start_pos[1] = center_pos[1] - LIGHT_LENGTH
        end_pos = [center_pos[0], 0]
        end_pos[1] = center_pos[1] + LIGHT_LENGTH
        roads.append(RedLightLink(start_pos, end_pos, LightColor.GREEN))

        # Verical Light roads
        start_pos = [0, 0]
        end_pos = [0, 0]
        start_pos = [center_pos[0], 0]
        start_pos[1] = center_pos[1] + LIGHT_LENGTH
        end_pos[0] = center_pos[0] + random.uniform(0, 100) - 50
        end_pos[1] = center_pos[1] + 50 + random.uniform(0, 50)
        points.append([end_pos[0], end_pos[1]])
        roads.append(Road(start_pos, end_pos))
        roads[3].add_end_link(roads[4], 0)
        
        start_pos = [0, 0]
        end_pos = [0, 0]
        start_pos[0] = center_pos[0] + random.uniform(0, 100) - 50
        start_pos[1] = center_pos[1] - 50 - random.uniform(0, 50)
        end_pos = [center_pos[0], 0]
        end_pos[1] = center_pos[1] - LIGHT_LENGTH
        points.append([start_pos[0], start_pos[1]])
        roads.append(Road(start_pos, end_pos))
        roads[5].add_end_link(roads[3], 0)
        
        return roads, points

class Stats:
    def average_network_knowledge() -> float:
        global road_manager, car_manager

        cars = car_manager.get_cars()
        total_percent = 0
        total_cars = len(cars)

        if total_cars == 0:
            return 0

        for car in cars:
            percent = Stats.get_car_knowledge_percent(car)
            total_percent += percent

        return total_percent / total_cars

    def get_car_knowledge_percent(car) -> float:
        global road_manager

        roads = road_manager.get_roads()
        router = car.router

        traveled_roads = router.get_traveled_roads()

        percent = float(len(traveled_roads)) / len(roads)
        return percent





clock = pygame.time.Clock()

TEST_AMOUNT = 5
for _ in range(TEST_AMOUNT):
    SIM_TICK = 0
    road_manager.reset()
    car_manager.reset()

    road_manager.generate_map()
    car_manager.spawn_cars(CAR_AMOUNT)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()

                car = car_manager.get_closest_car(pos)

                distance = tuple_distance(car.get_render_position(), pos)
                if distance < 20:
                    selected_car = car
                else:
                    selected_car = None

        clock.tick(60)
        SIM_TICK += 1
        screen.fill((255, 255, 255))

        # Only runs the simulation ticks until it hits the maximum
        if Stats.average_network_knowledge() < 1:
            road_manager.update_roads()
            car_manager.drive_cars()

        road_manager.render_roads(screen)
        car_manager.render_cars(screen)

        # render_gened_points(screen)
        print("%d %.3f" % (SIM_TICK, Stats.average_network_knowledge()))

        if SIM_TICK >= 5000:
            break

        pygame.display.flip()