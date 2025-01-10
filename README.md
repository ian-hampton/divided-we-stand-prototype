# Divided We Stand
Divided We Stand is a turn-based strategy game set in the modern era.
* Control your own unique nation with 8 governments and 4 foreign policies to pick from.
* Secure and develop regions to expand your nation.
* Negotiate and trade with other players.
* Form alliances with your allies and declare war on your enemies.
* Research new technologies and agendas to get an edge over your opponents.
* Win the game by completing your unique victory conditions before all other players.
* Supports up to 10 players.

<img src="app/static/preview.png" width="100%" alt="preview">

### Built With
* [Flask](https://flask.palletsprojects.com/en/stable/)
* [Pillow (PIL Fork)](https://pypi.org/project/pillow/)

<p align="right">(<a href="#divided-we-stand">back to top</a>)</p>



## Roadmap

- [x] Region code refactoring.
- [ ] Player code refactoring.
- [ ] Game management code refactoring.
- [ ] New frontend.
- [ ] Create a proper database to store all game data.
- [ ] New game maps.
    - [ ] British Isles?
    - [ ] China
    - [ ] Europe?
    - [ ] Southeast Asia?
- [ ] Public release? 👀

See the [open issues](https://github.com/ian-hampton/Divided-We-Stand/issues) to view proposed features and what is currently being worked on.

<p align="right">(<a href="#divided-we-stand">back to top</a>)</p>



## Development Environment Setup

### Prerequisites
* Install python virtualenv (if you do not already have it installed)
    ```sh
    pip install virtualenv
    ```

### Installation

1. Get into your directory of choice and clone the repo.
    ```sh
   git clone https://github.com/ian-hampton/Divided-We-Stand.git
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

<p align="right">(<a href="#divided-we-stand">back to top</a>)</p>



## Contact

Ian Hampton- ianhampton313@gmail.com

Project Link: [https://github.com/ian-hampton/Divided-We-Stand](https://github.com/ian-hampton/Divided-We-Stand)

<p align="right">(<a href="#divided-we-stand">back to top</a>)</p>



## Acknowledgments

* Vector data provided by [Natural Earth](https://www.naturalearthdata.com/about/).
* Raster data from NASA's [Blue Marble: Next Generation](https://earthobservatory.nasa.gov/features/BlueMarble).
* <details>
    <summary>Attribution for icons used</summary>
      <ul>
        <li><a href="https://www.flaticon.com/free-icons/missile" title="missile icons">Missile icons created by ranksol graphics - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/wind-energy" title="wind energy icons">Wind energy icons created by yoyonpujiono - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/power-plant" title="power plant icons">Power plant icons created by Dooder - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/solar" title="solar icons">Solar icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/control" title="control icons">Control icons created by hqrloveq - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/military-base" title="military base icons">Military base icons created by Ahmad Yafie - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/create" title="create icons">Create icons created by Ilham Fitrotul Hayat - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/sword" title="sword icons">Sword icons created by Good Ware - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/flag" title="flag icons">Flag icons created by Smashicons - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/flask" title="flask icons">Flask icons created by Bogdan Rosu - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/law" title="law icons">Law icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/graph" title="graph icons">Graph icons created by Gregor Cresnar - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/clipboard" title="clipboard icons">Clipboard icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/welcome" title="welcome icons">Welcome icons created by Uniconlabs - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/bank" title="bank icons">Bank icons created by Freepik - Flaticon</a></li>
        <li><a href="https://www.flaticon.com/free-icons/goverment" title="goverment icons">Goverment icons created by deemakdaksina - Flaticon</a></li>
      </ul>
  </details>
* Special thanks to everyone who has playtested the many early versions of this game:
  * Aidan Stubblebine
  * Alex Pham
  * Andrew Meyer
  * Charlie Nolan
  * David Abraham
  * Devin Abood
  * Izzy Beckhorn
  * Jacob Keith
  * Joey Badra
  * Kendal Hampton
  * Malcolm Hollingworth

<p align="right">(<a href="#divided-we-stand">back to top</a>)</p>