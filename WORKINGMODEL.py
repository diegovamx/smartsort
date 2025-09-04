from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes


pipeline = InferencePipeline.init(
   model_id="trash-sort-objd/1",
   #model_id="recyclesorting/1",  this model uses recycle, landfill, and compost but its not super accurate
    #model_id="garbage-lzfii/4",     this model uses recyclable, biodegradable, and residual but its less accurate

   video_reference=0,
   api_key="Mqg6MjfPG888hkIAilqR",
   on_prediction=render_boxes,
                  # Your Roboflow API key
   # The 'device' argument will default to 'cpu' on Raspberry Pi
)

pipeline.start()
pipeline.join()