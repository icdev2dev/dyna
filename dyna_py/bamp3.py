from baml_client import b

print (b.RAG("how to configure s3", ''' 
             # background 
             - the customer is interested in setting up s3 for lambda use
             # Use Cases
             ## how to setup  s3 (general  case)
             - login to console
             - look at s3
             ## how to setup s3 for AWS Lambda
             - ensure that you have a lambda function
             - configure s3 to trust s3
             # how to setup ec2
             - this is hard
             '''))
