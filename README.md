# Rules exporter

The alerts system of prometheus does not retrun when an alert is not firing. This exporter will get rules configured on the [inventory website](https://inventory.internal.unity3d.com/alerts/rules) and create a new metric with all rules up and firing in prometheus format.


## Rules 

We use labels to select rules in the list. To be consider, a rule have to have labels:

* **type**: cloud_health
* **service**: what ever the content, it will use in the global dashboard to group health status by services

## Configuration

|  Environment variable  |  Default Value  |  Required  |
|  --------------------- | --------------- | ---------- |
|  INVENTORY_URL         |  None           |    yes     |
|  INVENTORY_TOKEN       |  None           |    yes     |
|  INVENTORY_ENV         |  None           |    yes     |
|  EXPORTER_PORT         |  8000           |    no      |
|  LOG_LEVEL             |  info           |    no      |


## Development

Log in on [inventory website](https://inventory.internal.unity3d.com) and go to [rules list](https://inventory.internal.unity3d.com/alerts/rules). When you inspect the code with your browser in the network tab you will find the bear token ok api call


