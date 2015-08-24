__author__ = "Andrew Garcia <angarcia@marketo.com>"

import time
import httplib2
import json
import logging
import settings

# TODO

# Add return values to the Returns documentation
# Allow for integer parameters
# Non-English content for asset API
# Figure out how to fix the POST calls
# Standardize the comment syntax. Periods at the end of param descriptions?
# Do more elegant error handling
# Be more consistent with folder_id vs. folder
# Double check all the call URLs

class MarketoWrapper:
    """
    This class serves as a wrapper for the Marketo REST API. It is used
    in marketo_connector.py as the interface to a marketo instance.
    
    Attributes:
        __token (string):       The access token to be used to authenticate
                                API calls. 
        __expire_time (float):  When the access token expires and needs to be regenerated.
                                It is checked before every API call
        __http (httplib2.Http): The HTTP object the wraps all of the HTTP functionality required.
        __munchkin (string):    The munchkin ID of the Marketo instance
    """

############################################################################################
#                                                                                          #
#                                   Constructor                                            # 
#                                                                                          #             
############################################################################################

    def __init__(self, munchkin_id, client_id, client_secret):
        """
        The constructor performs all initialization as well as generates
        the first access token. All API calls will double check to make 
        sure the token is still valid before executing.
        
        Args:
            munchkin_id (string):    The munchkin ID of the Marketo instance
            client_id (string):      The client ID of the appropriate API user
            client_secret (string):  The client secret of the appropriate API user
        """
        self.__munchkin = munchkin_id
        # The httplib2.Http constructor takes an optional directory argument
        # where caching will be done. The directory does not need to exist beforehand.
        self.__http = httplib2.Http()
        # This will store credentials in __http so they do not need to be passed
        # each time a token is requested.
        self.__http.add_credentials(client_id, client_secret)
        # This value will be overwritten by _getAccessToken, so it is just
        # used for initialization
        self.__expire_time = 0
        self.__token = self.__generateAccessToken(self.__munchkin)

############################################################################################
#                                                                                          #
#                                   Private Methods                                        # 
#                                                                                          #             
############################################################################################
    
    def __generateAccessToken(self, munchkin_id):
        """
        This method requests a new access token from the REST API identity endpoint
        
        Note:
            The client ID and secret required to generate the token were added to the 
            __http attribute in the class constructor, so if the server requires authentication
            (it does), the httplib2 module does the credential handling automatically.
        
        Args:
            None
            
        Returns:
            string: The access token given by the server
        """
        # Request the token
        response, content = self.__http.request("https://"+self.__munchkin+
                                               ".mktorest.com/identity/"+
                                               "oauth/token?grant_type=client_credentials")
        # If the request was successful, return the token.
        if (response.status == 200):
            content = json.loads(content.decode("utf-8"))
            self.__reset_expire_time(content["expires_in"])
            return content["access_token"]
        else:
            print(str(response.status)+"\n"+response.reason)

    def __generic_api_call(self, call, method, content_type=None, payload=None, headers=None):
        """
        This method executes a generic API call to the REST API endpoint. The correct syntax
        should be passed into this method from inside of each call wrapper. 
        
        Args:
            call (string):                    The actual API call to make. This method contains the endpoint itself,
                                              but the desired call must be given from outside.
            method (string):                  The HTTP method to use (GET, POST, PUT etc.).
            content_type (string, optional):  What to set as the Content-type HTTP header
            payload (string, optional):       Any payload that should be sent to the server.
            headers (dict, optional):         Any custom headers to send. The access token is added automatically
                                              inside the method, so it does not need to be added manually from outside.
        
        Returns:
			dict: A dictionary representing the JSON response from the Marketo server.
        
        """
        # Default parameters in Python work differently than in other languages. See
        # this link for a full description: http://effbot.org/zone/default-values.htm
        if content_type is None:
            content_type = "application/json"
        if payload is None:
            payload = {}
        if headers is None:
            headers = {}
            
        # Check to see if the token has expired. If so, generate a new one.
        if self.__expire_time < time.time():
            self.__token = self.__generateAccessToken(self.__munchkin)
        
        # Add the access token to the HTTP header. 
        headers["Authorization"] = "Bearer "+self.__token
        # Prevents mismatch errors by exlicitly requesting json
        headers["Content-type"] = content_type
        # Make the API call.
        response, content = self.__http.request("https://"+self.__munchkin+".mktorest.com/"+
                                                    call, method, body=payload, headers=headers)
        
        # If the call was successful, return the content retrieved from the server.
        if (response.status == 200):
            return json.loads(content.decode("utf-8"))
        else:
            raise Exception(str(response.status)+"\n"+response.reason)
    
    def __reset_expire_time(self, expiresIn):
        """
        This method is used to reset the clock on an access token. When a new token is 
        generated, this method should be called with the "expires_in" field of the
        response from the Marketo identity endpoint. 
        
        Args:
            expiresIn (int):    The number of seconds until the new token expires. It should
                                be retrieved from the response of the Marketo identity endpoint
        """
        self.__expire_time = time.time() + expiresIn

############################################################################################
#                                                                                          #
#                                   Paging Token                                           # 
#                                                                                          #             
############################################################################################

    def get_paging_token(self, since_date_time):
        """
        This method is used to retrive a paging token from the Marketo database. Paging 
        tokens are for bulk API calls where the server needs to send multiple responses.
        This method should be used when initiating a bulk call, and the server will then
        return subsequent paging tokens in order to keep place inside the database.

        Args:
            since_date_time (string):    This is used to initiate the database search.
                                         It does not need to be any specific time, but
                                         it should be different than others used.
        Returns:
            string: The paging token given by the Marketo server
        """
        call = "rest/v1/activities/pagingtoken.json?sinceDatetime="+since_date_time
        method = "GET"
        response = self.__generic_api_call(call, method)
        return response["nextPageToken"]
	
############################################################################################
#                                                                                          #
#                                   Lead API Calls                                         # 
#                                                                                          #             
############################################################################################
    
	# TODO add the optional parameters
    def create_update_leads(self, leads):
        """
        This method makes takes an array of dictionaries that represent all of the leads
		and their attributes that should be updated in Marketo. It takes that array, and
		does an upsert operation to the Marketo database.
        
        Args:
            leads (list):   A list of dicts containing all of the leads to upload
            
        Returns:
            dict:   A dictionary that has the completion status for each lead in the input
        """
        call = "rest/v1/leads.json"
        method = "POST"
        payload = {"input": leads}
        # Use json.dumps() because the httplib2 does not serialize dictionary
        # objects by default.
        return self.__generic_api_call(call, method, json.dumps(payload))
        
    # TODO - add merge in CRM option and support multiple losers
    def merge_lead(self, winner, loser):
        """
        This method merges two or more leads. The winner's attributes will be preferred over the loser(s).
		Optionally, the leads can be merged in CRM as well.
        
        Args:
            winner (string):    The lead id of the authoritative lead
            losers (list):      A list of strings containing all of the lead ids to 
                                merge, but will yield to winner for conflicting values
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/v1/leads/"+leadID+"/merge.json"
        method = "POST"
        headers = {}
        headers["leadId"] = loser
        return self.__generic_api_call(call, method, None, headers)
    
    def get_lead_by_id(self, lead, fields=None):
        """
        This method retrieves a lead's attributes by its id. The fields parameter can specify 
		particular fields to return. The default return fields can be found in the developer's
		documentation.
        
        Args:
            lead (string):   			The id of the lead needed.
			fields (list, optional):	A list of fields to include in the response.
            
        Returns:
            dict:   A dictionary that contains all of the lead attributes
        """            
        call = "/rest/v1/lead/"+lead+".json"
        if fields is not None:
            call += "?fields="+fields
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_lead_activity_types(self):
        """
        This method returns all of the possible activity types.
        
        Args:
            None
            
        Returns:
            dict:   The response from the server. The "result" attribute contains an array 
					of dictionaries that represent each activity types. It includes the 
					activity id, name, attributes, description etc.
        """
        call = "/rest/v1/activities/types.json"
        method = "GET"
        return self.__generic_api_call(call, method)
	
    def get_lead_activities(self, activity_type_ids, paging_token, list_id=None, batch_size=None):
        """
        This method returns a list of lead activities that are filtered by the activity_type_ids
        parameter. That is, it returns all activities whose types match one of the types given
        in the parameter. The paging token is used because the list returned by the server may be 
        too large for a single response, and must be fragmented across responses. See this resource
        for more on paging tokens: http://developers.marketo.com/documentation/rest/get-paging-token

        Args:
            activitity_type_ids (list): A list of integers indicating the activity ids to filter on
            paging_token (string):		The paging token that will be used to iterate through the database
            list_id (int, optional):	The id of a list of leads to retrieve activities for
            batch_size (int, optional):	How many results the server will return at a time. Default and max
                                        is 300.

        Returns:
            dict:   The response from the server. The "result" attribute contains an array 
                    of dictionaries that represent the lead activities. They include the 
                    lead id, activity type id, primary attribute value etc.
        """
        call = 	"/rest/v1/activities.json?"+"nextPageToken="+paging_token
        if list_id is not None:
            call += "&listId="+str(list_id)
        if batch_size is not None:
            call += "&batchSize="+str(batch_size)
        for ii in range(len(activity_type_ids)):
            call += "&activityTypeIds="+str(activity_type_ids[ii])
        method = "GET"
        return self.__generic_api_call(call, method)
    
    #TODO - check for >300 activities
    def add_lead_activities(self, activities):
        """
        This method appends the given activities to the Marketo lead database.

        Args:
            activities (list):  A list of dicts containing all of the activites to upload.
                                The format should be of the following:
                                {         
                                    "leadId":1001,
                                    "activityDate":"2013-09-26T06:56:35+07:00",
                                    "activityTypeId":1001,
                                    "primaryAttributeValue":"Game Giveaway",
                                    "attributes":[  
                                        {  
                                           "name":"URL",
                                           "value":"http://www.nvidia.com/game-giveaway"
                                        }
                                    ]
                                }
                                Please see the developer documentation for more.

        Returns:
            dict:   The response from the server. The "result" attribute contains an array
                    of dictionaries that contain the completion status for each activity.
        """
        call = "rest/v1/activities/external.json"
        method = "POST"
        payload = {"input": activities}
        # Use json.dumps() because httplib2 does not serialize dictionary
        # objects by default.
        return self.__generic_api_call(call, method, json.dumps(payload))
	
############################################################################################
#                                                                                          #
#                                Campaign API Calls                                        # 
#                                                                                          #             
############################################################################################
    
    def schedule_campaign(self, camp_id, tokens=None, run_at=None, clone_to=None):
        """
        This method schedules a campaign to run inside of Marketo. The difference between
        schedule campaign and request campaign is that schedule campaign uses a smart list
        inside of Marketo whereas request campaign tells Marketo which leads to run through
        the campaign. 

        Args:
            camp_id (int):					The id of the campaign to be scheduled. This can be retrieved by
                                            making the get multiple campaigns call.
            tokens (list, optional):		A list of dictionaries that have the key/value pairs for the
                                            program tokens corresponding to that campaign. These tokens will
                                            not overwrite the ones configured in Marketo.
            run_at (string, optional):		A datetime string for when the campaign should run. If omitted,
                                            it defaults to five minutes in the future.
            clone_to (string, optional):	If this parameter is used, the parent program of the campaign will be
                                            cloned, and the newly created campaign will be the one to run.

        Returns:
            dict:   The response from the server that indicates success or failure.
        """
        call = "rest/v1/campaigns/"+camp_id+"/schedule.json"
        method = "POST"
        payload = {}
        if tokens is not None:
            payload["tokens"] = tokens
        if run_at is not None:
            payload["runAt"] = run_at
        if clone_to is not None:
            payload["cloneToProgramName"] = clone_to

        return self.__generic_api_call(call, method, json.dumps({"input": payload}))
    
############################################################################################
#                                                                                          #
#                                Folder API Calls                                          # 
#                                                                                          #             
############################################################################################
    
    def browse_folders(self, root, offset=None, max_depth=None, max_return=None, workspace=None):
        """
        This method returns a list of folders in Marketo. It is used to most commonly to retrieve 
		folder ids based on other folder information.
        
        Args:
            root (int):                     The id of the parent folder
            offset (int, optional):         Which index inside the parent to start from (default 0)
            max_depth (int, optional):      Maximum levels of recursion (default 2)
            max_return (int, optional):     Maximum folders to returns (default 20, max 200)
            workspace (string, optional):   Which workspace to search in
            
        Returns:
            dict:   The response from the server. The "result" attribute contains all of the 
					folder attributes for the folders in Marketo.
        """
        call = "rest/asset/v1/folders.json?root="+str(root)
        method = "GET"
        
        if offset is not None:
        	call += "&offSet="+str(offset)
        if max_depth is not None:
            call += "&maxDepth="+str(max_depth)
        if max_return is not None:
            call += "&maxReturn="+str(max_return)
        if workspace is not None:
            call += "&workSpace="+workspace
        
        return self.__generic_api_call(call, method)
    
    def get_folder_by_id(self, folder_id):
        """
        This method retrieves the metadata of the folder with the given id.
        
        Args:
            folder_id (int):    The id of the folder.
            
        Returns:
            dict:   The response from the server. The "result" attribute contains
					the same information that an individual result from the browse
					folders call.
        """
        call = "rest/asset/v1/folder/"+str(folder_id)+".json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_folder_by_name(self, folder_name, root=None, workspace=None):
        """
        This method retrieves the metadata of the folder with the given name.
        
        Args:
            folder_name (name):             The name of the folder
            root (int, optional):           The id of the parent folder
            workspace (string, optional):   The workspace that the folder is in
            
        Returns:
            dict:   The response from the server. The same data that is returned
					by the get folder by id call.
        """
        call = "rest/asset/v1/folder/byName.json?name="+folder_name
        method = "GET"
        
        if root is not None:
            call += "&root="+str(root)
        if workspace is not None:
            call += "&workSpace="+workspace
        
        return self.__generic_api_call(call, method)
    
    def create_folder(self, name, parent, description=None):
        """
        This method generates a folder inside of Marketo. Attributes such as
        type, isArchive, path etc. are inherited from the parent folder. 
        
        Args:
            name (string):                  The desired name of the folder
            parent (int):                   The id of the parent folder
            description (string, optional): A description of the folder
            
        Returns:
            dict:   The response from the server that indicates success or failure. It
					also includes the metadata similar to get folder by id, get folder by
					name, and browse folders.
        """
        call = "rest/asset/v1/folders.json?name="+name+"&parent="+str(parent)
        method = "POST"

        if description is not None:
            call += "&description="+description

        return self.__generic_api_call(call, method)
        
    def delete_folder(self, folder_id, folder_type):
        """
        This method deletes the folder with the given id.
        
        Args:
            folder_id (int):    	The id of the folder to be deleted
			folder_type (string):	Type of folder. Either "Folder" or "Program"
            
        Returns:
            dict:   The response from the server indicating success or failure. 
        """
        call = "rest/asset/v1/folder/"+str(folder_id)+"/delete.json"
        method = "POST"
        payload = "type="+folder_type
        return self.__generic_api_call(call, method, payload=payload)
    
    def update_folder(self, folder_id, folder_type, description=None, name=None, is_archive=None):
        """
        This method allows updating of the folder name, description and the option
        of archiving the folder.
        
        Args:
            folder_id (int):                The id of the folder to be deleted
			folder_type (string):			Type of folder. Either "Folder" or "Program"
            description (string, optional): The updated folder description
            name (string, optional):        The updated name of the folder
            is_archive (boolean, optional): Whether or not the folder should be archived.
            
        Returns:
            dict:   The response from the server that indicates success or failure. It
					also includes the metadata similar to get folder by id, get folder by
					name, and browse folders.
        """
        call = "rest/asset/v1/folder/"+str(folder_id)+".json"
        method = "POST"
        payload = {}
        if description is not None:
            payload["description"] = description
        if name is not None:
            payload["name"] = name
        if is_archive is not None:
            payload["isArchive"] = is_archive
        return self.__generic_api_call(call, method, payload=json.dumps(payload))
    
############################################################################################
#                                                                                          #
#                                 Token API Calls                                          # 
#                                                                                          #             
############################################################################################
        
    def create_token(self, parent_id, folder_type, token_type, name, value):
        """
        This method creates a token at the folder level or the program level.
        
        Args:
            parent_id (int):    	The id of the folder/program to place the token in
			folder_type (string):	Type of parent folder. Either "Folder" or "Program"
            token_type (string):	The type of the token. See below for list of types.
            name (string):      	The name of the token
            value (string):     	The value of the token. If it is a date token, it must
                                	be in the format yyyy-mm-dd. If it is a score, it must
                                	be preceeded by a +, - or = to indicate a score increment,
                                	decrement, or reset respectively.
            
        Returns:
            dict:   The response from the server that includes the calculated URL of 
					the new token.
            
        Available Data Types:
        
        date                A date value
        iCalendar           A .ics file
        number              An integer
        rich text           HTML text
        score               A score increment, decrement or reset
        script block        A Velocity script
        sfdc campaign       Used in SFDC campaign management integration
        text                Plain text
        
        *Types are case sensitive
        """
        call = "rest/asset/v1/folder/"+parent_id+"/tokens.json"
        method = "POST"
        payload = {"type": type,
                   "name": name,
                   "value": value}
        return self.__generic_api_call(call, method, payload=json.dumps(payload))
        
    def get_tokens(self, parent_id, folder_type):
        """
        This method lists all of the tokens under a folder/program
        
        Args:
            parent_id (int):    	The id of the folder/program where the tokens
                                	are located.
			folder_type (string):	Type of parent folder. Either "Folder" or "Program".
            
        Returns:
            dict:   The response from the server that includes the folder id and name, and 
					the token metadata.
        """
        call = "rest/asset/v1/folder/"+str(parent_id)+"/tokens.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def delete_tokens(self, parent_id, folder_type, name, token_type):
        """
        This method deletes a token from a folder/program.
        
        Args:
            parent_id (int):    	The id of the folder/program where the token is.
            folder_type (string):	Type of parent folder. Either "Folder" or "Program"/
            name (string):      	The name of the token
			type (string):      	The type of the token. See below for list of types.
            
        Returns:
            dict:   The response from the server indicating success or failure.
            
        Available Data Types:
        
        date                A date value
        iCalendar           A .ics file
        number              An integer
        rich text           HTML text
        score               A score increment, decrement or reset
        script block        A Velocity script
        sfdc campaign       Used in SFDC campaign management integration
        text                Plain text
        
        *Types are case sensitive
        """
        call = "rest/asset/v1/folder/"+parent_id+"/token/delete.json"
        method = "POST"
        payload = {"type": token_type,
                   "name": name}
        return self.__generic_api_call(call, method, payload=json.dumps(payload))
    
############################################################################################
#                                                                                          #
#                                  Email API Calls                                         # 
#                                                                                          #             
############################################################################################

    def get_emails(self, offset=None, max_return=None, status=None, folder=None):
        """
        This method gets a list of all the emails and their metadata
        from the Marketo instance.
        
        Args:
            offset (int, optional):		Specifies the start point. Can be used in conjunction
										with max_return to iterate through a large block of results.
			max_return (int, optional):	The maximum number of records to return. Default is 20 max 200.
			status (string, optional):	The status of the email asset. Either "Approved" or "Draft".
			folder (dict, optional):	A specific folder in which to search for emails. The dictionary
										should be of the following format:
											{
											 "id" : 1234,
											 "type" : "Folder"
											}
										where "id" is the folder id (integer), and "type" is either 
										"Program" or "Folder" (string).
            
        Returns:
            dict:   The response from the server. The "result" attribute has an array of dictionaries
					that represent the emails. It includes id, name, subject, from name, from email, 
					whether it is operational, whether it is published to MSI etc.
        """
        call = "rest/asset/v1/emails.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_by_id(self, email, status=None):
        """
        This method retrieves data about an email asset given its id.
        
        Args:
            email (int): 				The id of the desired email asset.
			status (string, optional): 	The status of the asset. Either "Approved" or "Draft". 
            
        Returns:
            dict:   The response from the server. The "result" attribute has an array of dictionaries
					that represent the email. It includes id, name, subject, from name, from email, 
					whether it is operational, whether it is published to MSI etc.
        """
        call = "rest/asset/v1/email/"+str(email)+".json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_content_by_id(self, email, status=None):
        """
        This method gets an email asset's content given its id. This does not include
        HTML. Email content in Marketo means the rich text that is contained in the
        editable sections. HTML must be acquired using the email template API.
        
        Args:
            email (int): 				The id of the desired email asset.
			status (string, optional):	The status of the asset. Either "Approved" 
										or "Draft"
            
        Returns:
            dict:   The response from the server that has the values of the editable
                    sections of the email. 
        """
        call = "rest/asset/v1/email/"+str(email)+"/content.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
############################################################################################
#                                                                                          #
#                             Email Template API Calls                                     # 
#                                                                                          #             
############################################################################################

    def get_email_templates(self, offset=None, max_return=None, status=None):
        """
        This method returns a list of all email templates and their metadata.
        
        Args:
            offset (int, optional):		Specifies the start point. Can be used in conjunction
										with max_return to iterate through a large block of results.
			max_return (int, optional):	The maximum number of records to return. Default is 20 max 200.
			status (string, optional):	The status of the email asset. Either "Approved" or "Draft".
            
        Returns:
            dict:   The response from the server. The "results" attribute is an array of dictionaries
                    that represent the email templates. It includes the id, the name, workspace, last
                    modified date etc.
        """
        call = "rest/asset/v1/emailTemplates.json"
        method = "GET"
        return self.__generic_api_call(call, method)

    def get_email_template_by_id(self, template_id, status=None):
        """
        This method returns the meta data of the given email template.
        
        Args:
            template_name (string):     The name of the desired email template.
            status (string, optional):  The status of the email asset. Either "Approved" or "Draft".
            
        Returns:
            dict:   The response from the server. It includes the same data as get_email_templates
                    just for the specific one given.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+".json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_template_by_name(self, template_name, status=None):
        """
        This method returns the meta data of the given email template.
        
        Args:
            template_name (string):     The name of the desired email template.
            status (string, optional):  The status of the email asset. Either "Approved" or "Draft".
            
        Returns:
            dict:   The response from the server. It includes the same data as get_email_templates
                    just for the specific one given.
        """
        call = "rest/asset/v1/emailTemplate/byName.json?name="+template_name
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_template_content_by_id(self, template_id, status=None):
        """
        This method returns the HTML of the given email template
        
        This method returns the meta data of the given email template.
        
        Args:
            template_id (int):          The name of the desired email template.
            status (string, optional):  The status of the email asset. Either "Approved" or "Draft".
            
        Returns:
            dict:   The response from the server. It includes the actual HTML of
                    the email template.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/content.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def update_email_template(self, template_id, name=None, description=None):
        """
        This method updates the name and/or description of the given email template.
        
        Args:
            template_id (string):             The id of the desired email template
            name (string, optional):          The new name of the email template
            description (string, optional):   The new description of the email template
            
        Returns:
            dict:   The response from the server that contains the updated
                    asset metadata.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+".json"
        method = "POST"
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        return self.__generic_api_call(call, method, payload=json.dumps(payload))
    
    def approve_email_template(self, template_id):
        """
        This method approves the given email template. This method also works on 
        drafts that are created underneath the given template.
        
        Args:
            template_id (int):   The id of the desired email template.
            
        Returns:
            dict:   The response from the server that includes the updated status.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/approveDraft.json"
        method = "POST"
        return self.__generic_api_call(call, method)      
    
    def unapprove_email_template(self, template_id):
        """
        This method unapproves the given email template.
        
        Args:
            template_id (id):   The id of the desired email template
            
        Returns:
            dict:   The response from the server that includes the updated status.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/unapprove.json"
        method = "POST"
        return self.__generic_api_call(call, method)    
    
    def delete_email_template(self, template_id):
        """
        This method deletes the given email template.
        
        Args:
            template_id (int):   The id of the desired email template
            
        Returns:
            dict:   The response from the server that indicates success or failure.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/delete.json"
        method = "POST"
        return self.__generic_api_call(call, method)
    
    def discard_email_template_draft(self, template_id):
        """
        This method discards the draft of the given email template.
        
        Args:
            template_id (int):   The id of the desired email template
            
        Returns:
            dict:   The response from the server indicating success or failure.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/discardDraft.json"
        method = "POST"
        return self.__generic_api_call(call, method)
    
#############################################################################################
# TODO - This is actually fine. It's the dictionary in the API call that is mucking things up
#############################################################################################
    
    def clone_email_template(self, template_id, name, folder):
        """
        This method clones the given email template.
        
        Args:
            template_id (string):   The id of the desired email template.
            name (string):          The name of the new email template.
            folder (string):        A specific folder in which to search for emails. The dictionary
                                    should be of the following format:
                                        {
                                         "id" : 1234,
                                         "type" : "Folder"
                                        }
                                    where "id" is the folder id (integer), and "type" is either 
                                    "Program" or "Folder" (string).
            
        Returns:
            dict:   The response from the server which includes all of the metadata
                    of the newly created asset.
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/clone.json"
        method = "POST"
        payload = {}
        payload["name"] = name
        payload["folder"] = folder
        return self.__generic_api_call(call, method, payload=json.dumps(payload))
    
############################################################################################
#                                                                                          #
#                                        Main                                              # 
#                                                                                          #             
############################################################################################
     
if __name__ == "__main__":
    logging.basicConfig(filename="logs.log", filemode="w", level=logging.DEBUG)
    munchkin = settings.MUNCHKIN
    client_id = settings.CLIENT_ID
    client_secret = settings.CLIENT_SECRET
    marketo = MarketoWrapper(munchkin, client_id, client_secret)
        
#    print(marketo.get_lead_by_id("5"))

    print(marketo.get_email_content_by_id(1108))

#    print(marketo.get_email_templates())
#    print(marketo.get_email_template_by_name("delete me"))
#    print(marketo.update_email_template("1011", description="sadfsdf"))
#    print(marketo.approve_email_template("1014"))
#    print(marketo.unapprove_email_template("1014"))
#    print(marketo.delete_email_template("1014"))
#    print(marketo.discard_email_template_draft("1014"))
#    print(marketo.clone_email_template("1014", "delete me clone", "15"))

#    print(marketo.browse_folders(129))
#    print(marketo.create_folder("delete me", 129))
#    print(marketo.delete_folder(178))
#    print(marketo.get_folder_by_id(129))
#    print(marketo.get_folder_by_name("Blog"))
#    print (marketo.update_folder(129, "stuff", "Blog Changed"))

#    print (marketo.get_tokens(129))
