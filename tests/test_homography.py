import pytest

from foresight.geometry.homography import HomographyProjector


def test_homography_projection_square():
    h = HomographyProjector(
        image_points=[[0,0],[100,0],[100,100],[0,100]],
        world_points_m=[[0,0],[1,0],[1,1],[0,1]],
    )
    assert h.image_point_to_table_xy([50,50]) == pytest.approx((0.5,0.5), abs=1e-6)
