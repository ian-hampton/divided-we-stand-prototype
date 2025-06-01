## Development Environment Setup

### Prerequisites
* Install python virtualenv (if you do not already have it installed)
    ```sh
    pip install virtualenv
    ```

### Installation

1. Get into your directory of choice and clone the dev branch.
    ```sh
   git clone -b dev --single-branch https://github.com/ian-hampton/divided-we-stand-prototype.git
   ```
2. Download image assets and paste them into the 'static' folder.  
    Note: Game archive images are currently unavailable.
    ```
    https://drive.google.com/drive/folders/1KX-A1SJXS72XJk-dEyoSqpg7B-2L_KMG?usp=sharing
    ```
3. Create a python virtualenv for this project using the provided requirements.txt file.
    1. cd into the root folder of your local repo.
        ```sh
        cd <repo>
        ```
    2. Create the virtual enviroment.
        ```sh
        python -m venv .venv
        ```
    3. Activate the virtual enviroment.
        ```sh
        source .venv\Scripts\activate
        ```
    4. Install project requirements.
        ```sh
        pip install -r requirements.txt
        ```