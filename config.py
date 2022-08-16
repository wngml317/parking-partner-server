class Config :
    JWT_SECRET_KEY = 'yhacademy1029##heelo'
    JWT_ACCESS_TOKEN_EXPIRES = False
    PROPAGATE_EXCEPTIONS = True

    # AWS uk
    ACCESS_KEY = 'AKIA2EOOWFSVZZWTLCP3'
    SECRET_ACCESS = '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'  

    # S3 버킷이름과, 기본 URL 주소 셋팅
    S3_BUCKET = 'uk-image-test'
    S3_LOCATION = 'https://uk-image-test.s3.amazonaws.com/'
