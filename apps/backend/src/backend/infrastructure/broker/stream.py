from faststream.nats import JStream

stream = JStream(name="stream", max_age=60 * 60, declare=True)
