from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import os
import shutil
import subprocess
import yaml


######################### HELPER FUNCTIONS #########################
def read_dojo_yml():
    with open('dojo.yml', 'r') as file:
        dojo_data = yaml.safe_load(file)
    return dojo_data

def write_dojo_yml(dojo_data):
    with open('dojo.yml', 'w') as file:
        yaml.safe_dump(dojo_data, file, sort_keys=False, allow_unicode=True)

def read_module_yml(module_id):
    module_path = os.path.join(module_id, 'module.yml')
    with open(module_path, 'r') as file:
        module_data = yaml.safe_load(file)
    return module_data

def write_module_yml(module_id, data):
    module_path = os.path.join(module_id, 'module.yml')
    with open(module_path, 'w') as file:
        yaml.safe_dump(data, file, sort_keys=False)

def is_module(folder):
    module_path = os.path.join(folder, 'module.yml')
    return os.path.exists(module_path)

def get_all_modules():
    dojo_data = read_dojo_yml()
    modules = dojo_data['modules']

    all_modules = []
    for module in modules:
        all_modules.append({'name': module['name'], 'value': module['id']})

    return all_modules

def get_modules_for_menu():
    all_modules = get_all_modules()
    
    modules = []
    for module in all_modules:
        modules.append(Choice(
            name=module['name'],
            value=module['id']
        ))

    return modules

def add_submodule_to_dojo_module(module_folder, submodule_url, submodule_name):
    """
    Adds a submodule to every challenge in a dojo's module. Skips if submodule already exists in challenge

    :param module_folder: Path to the module folder containing the challenges
    :param submodule_url: URL of the submodule repository
    :param submodule_name: Name of the submodule
    """
    # Ensure module folder exists
    if not os.path.isdir(module_folder):
        print(f"Module folder '{module_folder}' does not exist")
        return
    
    # Iterate through each challenge in the module folder
    for challenge in os.listdir(module_folder):
        challenge_path = os.path.join(module_folder, challenge)

        # Check if it's a directory
        if os.path.isdir(challenge_path):
            submodule_path = os.path.join(challenge_path, submodule_name)

            # Skip if the submodule folder already exists in the challenge
            if os.path.exists(submodule_path):
                print(f"Submodule '{submodule_name}' already exists in '{challenge_path}', skipping")
                continue

            # Add the submodule
            try:
                print(f"Adding submodule to '{challenge_path}'...")
                subprocess.run(['git', 'submodule', 'add', submodule_url, submodule_path], check=True)
                print('Done')
            except subprocess.CalledProcessError as e:
                print(f"Failed to add submodule to '{challenge_path}': {e}")

def is_dojo_initalized():
    # Checks if dojo.yml file exists
    if os.path.exists('dojo.yml'):
        return True
    
    # Checks if repo contains any folders with module.yml file in them
    folders = [d for d in os.listdir() if os.path.isdir(d)]
    for folder in folders:
        filepath = os.path.join(folder, 'module.yml')
        if os.path.exists(filepath):
            return True

    return False

def is_unique_new_entry(new, existing, type):
    new_id, new_name = new.get('id'), new.get('name')

    if new in existing:
        print(f"Error: A {type} with ID '{new_id}' and name '{new_name}' already exists.")
        return False
    
    for item in existing:
        if item.get('id') == new_id:
            print(f"Error: A {type} with ID '{new_id}' already exists.")
            return False
        elif item.get('name') == new_name:
            print(f"Error: A {type} with name '{new_name}' already exists.")
            return False

    return True


######################### INITIALIZE DOJO #########################
def init_dojo():
    # Initializes dojo.yml file
    dojo_name = inquirer.text(
        message='Enter dojo name (what will be displayed on pwn.college):'
    ).execute()
    dojo_id = dojo_name.lower().replace(' ', '-')

    dojo_type = inquirer.text(
        message='Enter dojo type:',
        default='roadshow'
    ).execute()

    # dojo_reward = inquirer.text(
    #     message='Enter dojo reward emoji:',
    # ).execute()

    confirm = inquirer.confirm(message='Do the dojo settings above look correct?').execute()

    if not confirm:
        print('Exiting dojo initialization')
        return
    
    print('Initializing dojo')
    dojo_data = {
        'id': dojo_id,
        'name': dojo_name,
        'modules': []
    }
    if dojo_type != '':
        dojo_data['type'] = dojo_type
    write_dojo_yml(dojo_data)


######################### CREATE MODULE #########################
def create_module():
    # Open the dojo.yml file
    dojo_data = read_dojo_yml()

    module_name = inquirer.text(
        message='Enter module name (what will be displayed on pwn.college):'
    ).execute()
    module_path = module_name.lower().replace(' ', '-')
    new_module = {'id': module_path, 'name': module_name}

    # Need to make sure that module doesn't already exist in dojo.yml
    existing_modules = dojo_data['modules']
    while not is_unique_new_entry(new_module, existing_modules, type='module'):
        choice = inquirer.select(
            message="What would you like to do?",
            choices=['Try a different module name', 'Quit']
        ).execute()
        
        if choice == 'Quit':
            print('Exiting module creation process')
            return
    
        module_name = inquirer.text(
            message='Enter module name (what will be displayed on pwn.college):'
        ).execute()
        module_path = module_name.lower().replace(' ', '-')
        new_module = {'id': module_path, 'name': module_name}

    # Confirm that module name looks correct
    confirm = inquirer.confirm(message='Do the above settings look correct?').execute()
    if not confirm:
        print('Exiting module creation process')
        return

    # Create module directory
    try:
        print(f"Creating directory '{module_path}'...", end='', flush=True)
        os.makedirs(module_path)
        print(' Done')
    except FileExistsError:
        print(' Error')
        print(f"Directory '{module_path}' already exists")
    except Exception as e:
        print(' Error')
        print(f'An error occurred trying to create the folder: {e}')

    # Add to dojo.yml modules
    print('Adding module to dojo.yml file...', end='', flush=True)
    dojo_data['modules'].append(new_module)
    write_dojo_yml(dojo_data)
    print(' Done')

    # Create module.yml file
    print('Creating module.yml file...', end='', flush=True)
    filepath = os.path.join(module_path, 'module.yml')
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.safe_dump({'name': module_name}, file, sort_keys=False)
    print(' Done')

    # Create DESCRIPTION.md file
    print('Creating DESCRIPTION.md file...', end='', flush=True)
    filepath = os.path.join(module_path, 'DESCRIPTION.md')
    with open(filepath, 'w'):
        pass
    print(' Done')


######################### CREATE CHALLENGE #########################
def create_challenge():
    # Display menu with module options
    modules = get_all_modules()
    if len(modules) == 0:
        print('No modules in dojo to delete, exiting now')
        return

    module_choice = inquirer.rawlist(
        message='Which module are you adding this challenge to?',
        choices=modules,
        default=None
    ).execute()

    # Read module.yml file
    module_data = read_module_yml(module_choice)
    if 'challenges' not in module_data:
        module_data['challenges'] = []

    # Get challenge name from user and generate challenge id
    challenge_name = inquirer.text(
        message='Enter challenge name:'
    ).execute()

    default_challenge_id = challenge_name.lower().replace(' ', '-')
    challenge_id = inquirer.text(
        message='Enter challenge ID:',
        default=default_challenge_id
    ).execute()

    new_challenge = {'id': challenge_id, 'name': challenge_name, 'allow_privileged': False}

    # Need to make sure that challenge doesn't already exist in module.yml
    existing_challenges = module_data['challenges']
    while not is_unique_new_entry(new_challenge, existing_challenges, type='challenge'):
        choice = inquirer.select(
            message="What would you like to do?",
            choices=['Try a different challenge name', 'Quit']
        ).execute()
        
        if choice == 'Quit':
            print('Exiting challenge creation process')
            return
    
        challenge_name = inquirer.text(
            message='Enter challenge name:'
        ).execute()

        default_challenge_id = challenge_name.lower().replace(' ', '-')
        challenge_id = inquirer.text(
            message='Enter challenge ID:',
            default=default_challenge_id
        ).execute()

        new_challenge = {'id': challenge_id, 'name': challenge_name, 'allow_privileged': False}

    # Confirm that challenge name looks correct
    confirm = inquirer.confirm(message='Is the above information correct?').execute()

    if not confirm:
        print('Exiting challenge creation process')
        return

    # Create challenge folder
    try:
        print(f"Creating directory '{challenge_id}'...", end='', flush=True)
        module_path = os.path.join(module_choice, challenge_id)
        os.makedirs(module_path)
        print(' Done')
    except FileExistsError:
        print(' Error')
        print(f"Directory '{challenge_id}' already exists")
    except Exception as e:
        print(' Error')
        print(f'An error occurred trying to create the folder: {e}')

    # Create DESCRIPTION.md file
    print('Creating DESCRIPTION.md file...', end='', flush=True)
    filepath = os.path.join(module_path, 'DESCRIPTION.md')
    with open(filepath, 'w'):
        pass
    print(' Done')

    # Create verify file with the following content:
    '''
    #!/usr/bin/exec-suid --real -- /usr/bin/python -I
    import sys
    sys.path.append('/challenge')

    def print_flag():
        try:
            with open("/flag", "r") as f:
                print(f.read())
        except FileNotFoundError:
            print("Error: Flag file not found.")

    # Add your imports and other code below here
    '''
    print('Creating verify file...', end='', flush=True)
    filepath = os.path.join(module_path, 'verify')
    # Make indents using 4 spaces instead of tabs
    indent = ' ' * 4
    with open(filepath, 'w') as file:
        file.write('#!/usr/bin/exec-suid --real -- /usr/bin/python -I\n')
        file.write("import sys\n")
        file.write("sys.path.append('/challenge')\n\n")
        file.write("def print_flag():\n")
        file.write(f"{indent}try:\n")
        file.write(f'{indent}{indent}with open("/flag", "r") as f:\n')
        file.write(f"{indent}{indent}{indent}print(f.read())\n")
        file.write(f"{indent}except FileNotFoundError:\n")
        file.write(f'{indent}{indent}print("Error: Flag file not found.")\n\n')
        file.write('# Add your imports and other code below here\n')
    print(' Done')

    # Add new challenge to module.yml file section
    module_data['challenges'].append(new_challenge)
    write_module_yml(module_choice, module_data)


######################### DELETE MODULE #########################
def delete_module():
    # Deletes folder and removes from dojo.yml
    modules = get_all_modules()

    if len(modules) == 0:
        print('No modules in dojo to select from, exiting now')
        return

    # Display menu with module options
    module_choice = inquirer.rawlist(
        message='Which module do you want to delete?',
        choices=modules,
        default=None
    ).execute()

    confirm = inquirer.confirm(
        message=f"Are you sure you want to delete the '{module_choice}' module?",
        default=False
    ).execute()

    if not confirm:
        print('Exiting delete module process')
        return

    # Delete folder
    if os.path.exists(module_choice):
        shutil.rmtree(module_choice)
        # Remove from modules list in dojo.yml
        dojo_data = read_dojo_yml()
        dojo_data['modules'] = [item for item in dojo_data['modules'] if item.get('id') != module_choice]
        write_dojo_yml(dojo_data)


######################### DELETE CHALLENGE #########################
def delete_challenge():
    # Delete from challenges in module.yml
    # Delete challenge folder in module folder
    modules = get_all_modules()
    if len(modules) == 0:
        print('No modules in dojo to select from, exiting now')
        return

    module_choice = inquirer.rawlist(
        message='Which module do you want to delete the challenge from?',
        choices=modules,
        default=None
    ).execute()

    # Get the list of challenges
    module_info = read_module_yml(module_choice)
    challenges = module_info['challenges']

    if len(challenges) == 0:
        print(f"No challenges in '{module_choice}' module to delete, exiting now")
        return

    choices = []
    for challenge in challenges:
        choices.append(Choice(
            name=challenge['name'],
            value=(challenge['id'], challenge['name'])
        ))
    choice = inquirer.select(
        message='Choose a challenge to delete:',
        choices=choices,
        default=None
    ).execute()
    challenge_id, challenge_name = choice

    confirm = inquirer.confirm(
        message=f"Are you sure you want to delete the challenge '{challenge_name}'",
    ).execute()

    if not confirm:
        print('Exiting challenge deletion process')
        return

    module_info['challenges'] = [item for item in module_info['challenges'] if item.get('id') != challenge_id]
    challenge_path = os.path.join(module_choice, challenge_id)
    if os.path.exists(challenge_path):
        write_module_yml(module_choice, module_info)
        shutil.rmtree(challenge_path)
    else:
        print('Challenge directory does not exist')


######################### ADD SUBMODULE #########################
def add_submodule():
    modules = get_all_modules()
    if len(modules) == 0:
        print('No modules in dojo to select from, exiting now')
        return

    module_choice = inquirer.rawlist(
        message='Which module do you want to add the submodule to?',
        choices=modules,
        default=None
    ).execute()

    submodule_url = inquirer.text(
        message='Enter submodule URL:'
    ).execute()

    default_submodule_name = submodule_url.split('/')[-1]
    submodule_name = inquirer.text(
        message='Enter submodule name:',
        default=default_submodule_name
    ).execute()

    confirm = inquirer.confirm(
        message=f'Warning: This will add the submodule to every challenge in the {module_choice} module. Are you sure you want to proceed?'
    ).execute()

    if not confirm:
        print(f'Not adding submodule {submodule_name} to {module_choice} module')
        return
    
    print(f'Adding submodule {submodule_name} to {module_choice} module')
    add_submodule_to_dojo_module(module_choice, submodule_url, submodule_name)


######################### DISPLAY MENU #########################
def display_menu():
    choices = [
        Choice(name='Edit Modules', value='module'),
        Choice(name='Edit Challenges', value='challenge'),
        Choice(name='Quit', value=None)
    ]

    # Only display option to initialize if dojo.yml doesn't exist and no folders (modules) exist in repo
    initialized = is_dojo_initalized()
    if not initialized:
        choices.insert(0, Choice(name='Initialize Dojo', value=init_dojo))

    choice = inquirer.rawlist(
        message='Choose an option:',
        choices=choices,
        default=1
    ).execute()

    if choice == 'module':
        choice = inquirer.rawlist(
            message='Choose a module option:',
            choices=[
                Choice(name='Create', value=create_module),
                Choice(name='Add Submodule', value=add_submodule),
                Choice(name='Delete', value=delete_module),
                Choice(name='Go Back', value=display_menu)
            ],
            default=1
        ).execute()
    elif choice == 'challenge':
        choice = inquirer.rawlist(
            message='Choose a challenge option:',
            choices=[
                Choice(name='Create', value=create_challenge),
                Choice(name='Delete', value=delete_challenge),
                Choice(name='Go Back', value=display_menu)
            ],
            default=1
        ).execute()

    if choice:
        choice()


if __name__ == '__main__':
    display_menu()