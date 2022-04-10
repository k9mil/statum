from statum import scheduler, create_app
from statum.main.utils.utils import random_stream

@scheduler.task('interval', id='periodic_index_clearance', seconds=300, misfire_grace_time=360)
def periodic_index_clearance():
    app = create_app()
    with app.test_request_context():
        random_stream()