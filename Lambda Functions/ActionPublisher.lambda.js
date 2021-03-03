var AWS = require('aws-sdk');
var iotdata = new AWS.IotData({endpoint: 'a1d9vpf5euf4oe-ats.iot.us-east-1.amazonaws.com'});

exports.handler = async (event, context) => {
  let payload = JSON.parse(event.body);
  
  console.log(`Sending to: ${payload.device}`);
  console.log(`Body: ${payload}`);

  var params = {
    topic: `device/actions`,
    payload: JSON.stringify(payload),
    qos: 0
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify(await publishMessage(params))
  }
} 

const publishMessage = async (params) => {
  return new Promise((resolve, reject) => {
    iotdata.publish(params, function(err, data) {
      if(err) {
         reject(err)
      } else {
         resolve(params)
      }
    })
  });
}