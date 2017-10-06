from __future__ import print_function # Python 2/3 compatibility
import os
import hashlib
import boto3
import json
import decimal
import uuid
import random
import logging
import datetime
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    limit = float(os.environ["matchingSensitivity"]) #Lowest acceptable value for matching to a group
    group_limit = int(os.environ["group_size"]) #Maximum number of users in one group
    totalExpectedUsers=int(os.environ["totalExpectedUsers"]) #Expected total number of users that will be matched to groups
    #Database: 
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    groupLabelTable = dynamodb.Table('groupLabelMap')
    userGroupTable = dynamodb.Table("UserGroupMappings")
    groupsTable = dynamodb.Table("Groups")
    userProfilesTable = dynamodb.Table('UserProfiles')
    questionsTable = dynamodb.Table('Questions')
    matchingStatisticsTable = dynamodb.Table('matchingStatistics')

    #For invoking other lambda functions
    lambda_client = boto3.client('lambda')
    
    #Logging
    logger=logging.getLogger()
    logger.setLevel(logging.INFO)

    #Helper-functions:
        #Function for authenticating the signature from the QR-code
    def authenticateQRsignature(user, signature):
        superSecretKey = os.environ['hashKey']
        hash = hashlib.sha224((superSecretKey + user).encode('utf-8')).hexdigest()
        if (signature == hash):
            return True
        else:
            return False
            
        #Function for genrating a unique identifier when creating new groups
    def generateGroupID():
        return str(uuid.uuid4())
    
        #Method that creates a maping between a groupID and a label in the database
    def mapGroupToLabel(groupID):
        urlToUpdate=""
        #Find the first free labelUrl in the database:
        validUrls = groupLabelTable.scan()['Items']
        random.shuffle(validUrls)
        for i in validUrls:
            if(i.get("groupID")==" "):
                urlToUpdate=i.get("labelUrl")
                break

        #This will happen if there are no free labels available  
        if(urlToUpdate==""):
            #Reset all labels
            invoke_response = lambda_clientlambda_client.invoke(FunctionName="clearLabelGroupMapping",
                                                   InvocationType='RequestResponse'
                                                  )
            # Then find the first free labelUrl in the database:
            validUrls = groupLabelTable.scan()
            for i in validUrls['Items']:
                if(i.get("groupID")==" "):
                    urlToUpdate=i.get("labelUrl")
                    break

        #Assign the free labelUrl to the groupID:
        groupLabelResponse = groupLabelTable.update_item(
            Key={
                "labelUrl": urlToUpdate
            },
            UpdateExpression="set groupID = :r",
            ExpressionAttributeValues={
                ":r": groupID
            }
        )
        return urlToUpdate
    
        #Method for creating a mapping between a group and a user in the database
    def assignUserToGroup(group, userID, isRandomAssignment):
        
        groupAdded = userGroupTable.put_item(
        Item={
                "groupID": group.get("groupID"),
                "userID":userID,
                "isRandomAssignment":isRandomAssignment,
                "label":getLabelURLFromGroupID(group.get("groupID"))
            }
        )
            
        
        if(group.get("numberOfUsers")>=group_limit-1):
            
            #Delete group
            response = groupsTable.delete_item(
                Key={
                    'groupID': group.get("groupID")
                }
            )
        else:
            #Count one more user in group
            
            groupCountUpdate = groupsTable.update_item(
                Key={
                    "groupID": group.get("groupID")
                },
                UpdateExpression="ADD numberOfUsers :i",
                ExpressionAttributeValues={
                    ":i":1
                }
            )
            
        return group.get("groupID")
    
        #Function that creates a new group and returns the groupID for the group
    def createNewGroup(firstUser, isRandomAssignment):
        guid=generateGroupID()
        groupCreated = userGroupTable.put_item(
        Item={
                "groupID": guid,
                "userID":firstUser,
                "isRandomAssignment":isRandomAssignment,
                "label":mapGroupToLabel(guid)
            }
        )
        
        #Query for creating the group in the Groups-table
        
        group = groupsTable.put_item(
        Item={
                "groupID": guid,
                "groupAverage":getUserAnswers(firstUser),
                "numberOfUsers":1
                
            }
        )

        return guid

        #Function for getting answers from the database for a specific user 
    def getUserAnswers(userID):
        

        userProfile = userProfilesTable.get_item(
            Key={
            "userID": userID
            }
        )
        #If no answers exists for the user, return random answers, based on existing group categories
        if(userProfile.get("Item")==None):
            dict={}
            
            questions = questionsTable.scan()
            for question in questions.get("Items"):
                dict[question.get("group")+question.get("Type")]=str(random.randint(1,3))
            return dict
        return userProfile.get("Item").get("answers")

        #Function that gets all available groups from the database
    def getGroups():
        groups = groupsTable.scan() 
        return groups.get("Items")
        
        #Function that gets the grup for a user, if the user does not have a group None will be returned
    def getGroupForUser(userID):
        group = userGroupTable.get_item(
        Key={
            "userID":userID
        })
        return group.get("Item")

        #Function that calculates how good a user fits in a group (does the matching-calculation)
    def matchGroup(userAnswers, group):
        numberOfEquals=0
        groupAverage=group.get("groupAverage")
        
        try:
            if(group.get("groupID")==event.get("doNotAssignTo")):
                return 0
        except:
            print("The printer did not supply a doNotAssignTo-value")

        for category, answer in userAnswers.items():
            if(str(userAnswers[category])==str(groupAverage[category])):
                numberOfEquals+=1
        return numberOfEquals/len(userAnswers)
        
        #Function that gets the label associated with a group
    def getLabelURLFromGroupID(groupID):
        validUrls = groupLabelTable.scan()
        for i in validUrls.get("Items"):
            if(i.get("groupID")==groupID):
                return i.get("labelUrl")
        
        return "No URL found"
    
        #If a user has not answered any questions this function puts the user in a random group
    def assignUserRandomly(userID, maxUserCount, groups):
        if(len(groups)<8): #This to avoid that all random users get placed in the same group if there are no groups available
            
            #Update statistics table
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count2 = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD numberOfMatchingGroupsCreated :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            except:
                logger.info("Saving matching-statistics failed")

            return createNewGroup(userID, True)
        groupIndex=random.randint(0,len(groups)-1)
        for i in range(100): #Set to 100 attempts before a new group is created
            if(groups[groupIndex].get("numberOfUsers")<maxUserCount):
                return assignUserToGroup(groups[groupIndex], userID, True)
                break
        
        #Create a new group instead
        return createNewGroup(userID, True)

    #Object to return:
    response={}

    #Check that the QR provided is valid
    try:
        splitString = event["signature"].split(".")

        userID=splitString[0]
        signature=splitString[1]
    except:
        response["authentication"]=False
        logger.info("No groupID returned due to invalid QR")
        response["message"]="No groupID returned due to invalid QR"
        response["groupID"]=""
        response["labelToPrint"] =""
        return response

    if(authenticateQRsignature(userID, signature)):
        response["authentication"]=True
    else:
        logger.info("No groupID returned due to invalid QR")
        response["authentication"]=False
        response["message"]="No groupID returned due to invalid QR"
        response["groupID"]=""
        response["labelToPrint"] =""
        return response
    
    #Main function for initiating the entire matching
    def main():
        try:
            logger.info("Received event: "+str(event))
        except:
            logger.info("Failed receiving event")
        groups=getGroups()

        #Check if the user already has a group
        groupForUser=getGroupForUser(userID)
        if(groupForUser!=None):
            returnGroup=groupForUser.get("groupID")
            response["message"]="The user already has a group, the groupID for this group is returned"
            response["groupID"]=returnGroup
            response["labelToPrint"] = groupForUser.get("label")
            logger.info("The user already has a group, the groupID for this group is returned")
            
            #Update statistics table
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD totalNumberOfScans :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            
            except:
                logger.info("Saving matching-statistics failed")
            
            return response

        #Check that the user has delivered answers in booth

        userProfile = userProfilesTable.get_item(
            Key={
            "userID": userID
            }
        )
        if(userProfile.get("Item")==None):
            returnGroup=None
            try:
                returnGroup=assignUserRandomly(userID, group_limit, groups)
            except:
                returnGroup=createNewGroup(userID, True)
                #Update statistics table
                try:
                    today=datetime.datetime.today()+datetime.timedelta(hours=2)
                    count2 = matchingStatisticsTable.update_item(
                        Key={
                            "date": str(today.date())
                        },
                        UpdateExpression="ADD numberOfMatchingGroupsCreated :i",
                        ExpressionAttributeValues={
                            ":i":1
                        }
                    )
                except:
                    logger.info("Saving matching-statistics failed")
                
            response["message"]="User has not used the vennskaper-booth, group assigned randomly"
            response["groupID"]=returnGroup
            response["labelToPrint"] = getLabelURLFromGroupID(returnGroup)
            logger.info("User has not used the vennskaper-booth, group assigned randomly")

            #Update statistics table
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD totalNumberOfScans :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )

                count2 = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD numberOfRandomAssignments :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            
            except:
                logger.info("Saving matching-statistics failed")

            return response

        #Check if there are no groups in database
        if(len(groups)==0):
            returnGroup=createNewGroup(userID, False)
            response["message"]="There are no groups in the database, a new group has been created for the user"
            response["groupID"]=returnGroup
            response["labelToPrint"] = getLabelURLFromGroupID(returnGroup)
            logger.info("There are no groups in the database, a new group has been created for the user")
            
            #Update statistics table
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD totalNumberOfScans :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )

                count2 = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD numberOfMatchingGroupsCreated :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            
            except:
                logger.info("Saving matching-statistics failed")

            return response

        #Initiate matching algorithm to find the best matching group
        
        best = 0 #Variable which holds the matching-value for the best group so far
        answers=getUserAnswers(userID) #Answers for the users, used for matching to group
        bestGroup="" #Variable that holds the best group so far
        
        for group in groups:
            mg = matchGroup(answers, group)
            if mg >= best and group.get("numberOfUsers") < group_limit:
                best = mg
                bestGroup=group
        if ((best >= limit) ):
            #Add to best group
            returnGroup=assignUserToGroup(bestGroup,userID, False)
            response["groupID"]=returnGroup
            response["labelToPrint"] = getLabelURLFromGroupID(returnGroup)
            response["message"]="A suitable group was found for the user, the match-value was "+str(best)
            logger.info("A suitable group was found for the user, the match-value was "+str(best))

            #Update statistics table
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD totalNumberOfScans :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            
            except:
                logger.info("Saving matching-statistics failed")

            return response
        elif(len(groups)>int((totalExpectedUsers/group_limit/4)+2)): #This to avoid to many unfilled groups
            #Add to best group, there are too many unfilled groups
            returnGroup=assignUserToGroup(bestGroup,userID, False)
            response["groupID"]=returnGroup
            response["labelToPrint"] = getLabelURLFromGroupID(returnGroup)
            response["message"]="Too many unfilled groups, user forced into group, the match-value was "+str(best)
            logger.info("Too many unfilled groups, user forced into group, the match-value was "+str(best))

            #Update statistics tableus
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD totalNumberOfScans :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            
            except:
                logger.info("Saving matching-statistics failed")

            return response
        else:
            #Create a new group
            returnGroup=createNewGroup(userID, False)
            response["groupID"]=returnGroup
            response["labelToPrint"] = getLabelURLFromGroupID(returnGroup)
            response["message"]="No suitable group was found, a new group was created for the user, best match-value was "+str(best)
            logger.info("No suitable group was found, a new group was created for the user, best match-value was "+str(best))

            #Update statistics table
            try:
                today=datetime.datetime.today()+datetime.timedelta(hours=2)
                count = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD totalNumberOfScans :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )

                count2 = matchingStatisticsTable.update_item(
                    Key={
                        "date": str(today.date())
                    },
                    UpdateExpression="ADD numberOfMatchingGroupsCreated :i",
                    ExpressionAttributeValues={
                        ":i":1
                    }
                )
            
            except:
                logger.info("Saving matching-statistics failed")

            return response
    #return main()
    
    try:
        return main()
    except:
        #Backup solution:
        logger.error("The matching algorithm failed due to an error, returning random group assignment as backup")
        groups=getGroups()
        if(authenticateQRsignature(userID, signature)):
            response["authentication"]=True
            returnGroup=assignUserRandomly(userID, group_limit, groups)
            response["message"]="The matching algorithm failed due to an error, returning random group assignment as backup"
            response["groupID"]=returnGroup
            response["labelToPrint"] = getLabelURLFromGroupID(returnGroup)
            return response
        else:
            response["authentication"]=False
            response["message"]="No groupID returned due to invalid QR"
            logger.info("No groupID returned due to invalid QR")
            return response
        
    '''
    def test():
        #return matchGroup("24478f62-69e4-4bfb-b4be-2a0cb6178deb","e3ff9e50-5453-449b-a57b-de7dda2b6d5b")
        #return getGroupForUser("testUser")
        return main()
    return test()
    '''
    
    