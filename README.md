# RedAnt_Test

### Structure:

redant_libs: consists of the libs and ops that will help in running the test cases.<br>
tests: holds the test cases. Add any new test cases here.<br>

### To start Working:

1. Clone the odinControl inside the RedAnt_Test. [This is temporary. Once odinControl is converted into a python package we won't need this step]. You can directly call the rexe from the odinControl or use a directory rexe where you can put **__init__.py** and **rexe.py** and hence call the file.

2. Create a **Utilities** folder and add **conf.yaml** file [This is temporary as well just for testing. Once we are ready with the components we just need to connect them.]
 OR
 You can also call the conf.yaml from the odinControl. I have used it here just to indicate the independence of each component. But reusability of existing files won't hurt. :sweat_smile:


### STEP-BY_STEP procedure to run:
1. git clone `[your fork for this repo]`
2. cd `[the-fork]`
3. git clone [odinControl](https://github.com/srijan-sivakumar/odinControl.git)
4. cd `odinControl` && mkdir `rexe` && cp `rexe.py` `rexe/rexe.py` && touch `rexe/__init__.py`
5. cd ..
6. mkdir `Utilities` && touch `Utilities/conf.yaml`
7. Add the following in `conf.yaml`:

```javascript
host_list: [server IPs]
user: "user"
passwd: "pass"
```
8. python3 `redant_libs/peer_ops.py`
