# Dojo Template

Use this template to make new dojos!

## Before running `manage_dojo.py` for first time
```commandline
pip install inquirerpy
pip install PyYAML
```

## Dojo YAML File
```yaml
id: # ID of the dojo (lowercase version of name with hyphens replacing spaces)
name: # Dojo Name
type: # What category to put the dojo under (for example: roadshow)
award:
  emoji: # Emoji award to give user upon dojo completion
modules:
- id: example # Module ID
  name: Example # Module Name
```

## Module YAML File
```yaml
name: # module name - displayed in the web page (should have spaces, uppercase as needed)
challenges: # list each challenge, make a directory for each challenge (must match the id)
  - id: # lowercase, no spaces
    name: # short descriptive name of the challenge
    allow_privileged: # true allows practice mode, false hides practice mode
    # There are more flags like "password" that are not listed here
  - id: example
    name: This is an Example Module
    allow_privileged: false
```

## Automatic Dojo Updates
After completing the following steps, your dojo in our production version of pwncollege will be automatically updated whenever you make a push to the `main` branch.

NOTE: To do this, your dojo has to already be added to the production version of [our pwncollege instance](https://pwncollege.arl.madren.org/). If it hasn't been, you'll have to manually add it the first time.

### Setting the `dojo` field
- Reference ID of your dojo
  - For example: `official-dojo` or `unofficial-dojo~1a2b3c4d`
- Found on the `admin` page of dojo
- Copy and paste this value into the `dojo` field in the `.github/workflows/update.yml` file

### Creating the `UPDATE_CODE` secret
To get the dojo's update code, go to the `Admin` page of your dojo, hover over the `Update` button, and copy the URL. The last part of the URL is the update code. It will look like
```
https://pwncollege.arl.madren.org/dojo/DOJO_NAME/update/UPDATE_CODE
```

To add the update code as a GitHub secret:
1. In dojo repository, click on `Settings`
2. On the left side under `Security`, click on `Actions`
3. Under `repository secrets`, create `UPDATE_CODE` secret if it doesn't exist in your repository by clicking `New repository secret`:
    1. Click `New repository secret`
    2. Set `name` to be `UPDATE_CODE`
    3. Paste in the copied URL and delete everything except the update code at the end
4. If the secret already exists in the repository:
    1. Click the edit button (pencil icon) in the same row as `UPDATE_CODE`
    2. Paste in the copied URL and delete everything except the update code at the end
    3. Click `Update secret`

### Reference
[pwncollege/dojo-update](https://github.com/pwncollege/dojo-update)