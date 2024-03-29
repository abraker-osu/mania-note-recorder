# mania-note-recorder

### What is this?

This is a tool made to record multiple scores on the same map. After playing a map multiple times, it shows the average hit timing for each note. Graphs/displays can be moved around using left click drag, and zoomed in/out using right click drag

![image](https://github.com/abraker-osu/mania-note-recorder/assets/4358724/75439695-c25a-4f63-864a-2cbeb215498b)

### Running from source:

1. You will need git. You can download it here: https://git-scm.com/

2. You will need python, at least version 3.8. You can download it here: https://www.python.org/downloads/. THERE IS A STEP THAT ASKS WHETHER TO ADD TO PATH. MAKE SURE TO CHECK THAT.

3. Once git is installed, create a folder somewhere where the tool will reside in (desktop or documents, doesn't matter)

4. In windows explorer, go to the newly created folder. Then in the address bar enter in "cmd". A command prompt window should pop up.

5. Run the following command. This will download the project:
```
git clone -v --recurse-submodules --progress "https://github.com/abraker-osu/mania-note-recorder.git" "."
```

6. Run the following command. This will install the needed libraries to run the tool:
```
pip install -r requirements.txt
```
If that fails, use:
```
python3 -m pip install -r requirements.txt
```

7. Open run.py in text editor or something and change the osu path you see to the one you have. Make sure to change back slashes to forward slashes if there are any.

8. Run the tool with the following command:
```
python3 run.py
```

9. Play any map of your choosing (HT, DT, MR mods supported). DONT MIX HT/DT MODS.

NOTE: Scoring processor has a tendency to break if you mash, so don't play anything too ridiculously hard. I am trying to fix that bug.
