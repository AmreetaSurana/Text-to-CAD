import cadquery as cq

base_size = max(0.1, 100)
base_height = max(0.1, 200)

part = (
    cq.Workplane("XY")
    .rect(base_size, base_size)
    .extrude(base_height)
)

feature1_radius = max(0.1, 40)
feature1_height = max(0.1, 50)
feature1_pos_x = 50
feature1_pos_y = 50
feature1_pos_z = 200

feature1 = (
    cq.Workplane("XY")
    .center(feature1_pos_x, feature1_pos_y)
    .circle(feature1_radius)
    .extrude(feature1_height)
    .translate((0, 0, feature1_pos_z))
)

feature2_radius = max(0.1, 30)
feature2_height = max(0.1, 20)
feature2_pos_x = 50
feature2_pos_y = 50
feature2_pos_z = 250

feature2 = (
    cq.Workplane("XY")
    .center(feature2_pos_x, feature2_pos_y)
    .circle(feature2_radius)
    .extrude(feature2_height)
    .translate((0, 0, feature2_pos_z))
)

assembly = part.union(feature1).union(feature2)