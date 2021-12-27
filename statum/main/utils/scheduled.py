from statum import scheduler, create_app, database
from statum.main.utils.utils import randomStream

@scheduler.task('interval', id='periodicIndexClearence', seconds=300, misfire_grace_time=360)
def periodicIndexClearence():
    database.random_streamer_data.remove()
    app = create_app()
    with app.test_request_context():
        randomStream()