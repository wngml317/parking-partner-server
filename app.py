from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from resources.parking import ParkingResource, ParkingListResource, ParkingInfoResource
from resources.user import UserLoginResource, UserLogoutResource, UserRegisterResource, jwt_blacklist


app = Flask(__name__)

# 환경변수 셋팅
app.config.from_object(Config)

# JWT 토큰 라이브러리 만들기
jwt = JWTManager(app)

# 로그아웃 된 토큰이 들어있는 set을, jwt 에 알려준다.
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in jwt_blacklist

api = Api(app)

api.add_resource(UserRegisterResource, '/users/register')
api.add_resource(UserLoginResource, '/users/login')
api.add_resource(UserLogoutResource, '/users/logout')
api.add_resource(ParkingResource, '/parking')
api.add_resource(ParkingListResource, '/parkingList')
api.add_resource(ParkingInfoResource, '/parking/<string:prk_center_id>')


if __name__ == '__main__' :
    app.run()