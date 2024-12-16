from app import app
import cProfile

if __name__ == '__main__':
    cProfile.run('app.run(debug=False)', 'flask_profile.prof')