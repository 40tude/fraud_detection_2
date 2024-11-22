```
conda activate producer_nodocker
./secrets.ps1
session.timeout.ms=45000 commented in clients.properties
```

* faut faire `producer.flush()` pour que on_produce() soit appelée

```python
producer.produce(k_Topic, key=k_Key, value=json.dumps(data).encode("utf-8"), callback=on_produce)
producer.flush()
```