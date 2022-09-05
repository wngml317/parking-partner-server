from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from facility import Facility
from resources.parking import ParkingResource, ParkingListResource, ParkingInfoResource , ParkingEndResource ,ParkingLctResource
from resources.review import ParkingReviewResource, ParkingReviewInfoResource, ReviewCntResource
from resources.parkComplete import DetectTextResource, ParkingCompleteResource
from resources.user import UserLoginResource, UserLogoutResource, UserRegisterResource, jwt_blacklist
from resources.endParking import ParkingPayResource



app = Flask(__name__)

# 환경변수 셋팅
app.config.from_object(Config)
app.config['TIMEOUT'] = 60 #second

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
api.add_resource(DetectTextResource, '/upload')
api.add_resource(ParkingCompleteResource, '/parkingComplete')
api.add_resource(ParkingEndResource, '/end')
api.add_resource(ParkingLctResource, '/parkLct/<int:parking_id>')
api.add_resource(ReviewCntResource, '/mypage')
api.add_resource(ParkingReviewResource, '/review')
api.add_resource(ParkingReviewInfoResource, '/review/<int:review_id>')
api.add_resource(ParkingPayResource,'/parkingend/<int:parking_id>')

api.add_resource(Facility, '/facility')

#host="192.168.0.167",port=5000
if __name__ == '__main__' :
    app.run()