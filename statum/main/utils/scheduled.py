from statum import scheduler, create_app
from statum.main.utils.utils import randomStream

@scheduler.task('interval', id='periodicIndexClearence', seconds=300, misfire_grace_time=360)
def periodicIndexClearence():
    app = create_app()
    with app.test_request_context():
        randomStream()