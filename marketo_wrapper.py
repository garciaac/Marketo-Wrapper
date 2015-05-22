__author__ = "Andrew Garcia <angarcia@marketo.com>"

import time
import httplib2
import json
import logging
import poster
import settings
from urllib import urlencode

# TODO

# Add return values to the Returns documentation
# Allow for integer parameters

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
        self.__http = httplib2.Http(".http_cache")
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
        
        
        print(call)
        print(method)
        print(content_type)
        print(payload)
        print(headers)
        
        
        # Make the API call.
        response, content = self.__http.request("https://"+self.__munchkin+".mktorest.com/"+
                                                    call, method, body=payload, headers=headers)
        
        # If the call was successful, return the content retrieved from the server.
        if (response.status == 200):
            return content
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
#                                   Lead API Calls                                         # 
#                                                                                          #             
############################################################################################
    
    def create_update_leads(self, leads):
        """
        This method makes the create_update_leads call.
        
        Args:
            leads (list):   A list of dicts containing all of the leads to upload
            
        Returns:
            dict:   The response from the server
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
        This method makes the merge_lead call.
        
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
    
    def get_lead_by_id(self, lead):
        """
        This method makes the get_lead_by_id call.
        
        Args:
            lead (string):   The id of the lead needed
            
        Returns:
            dict:   The response from the server
        """
        call = "/rest/v1/lead/"+lead+".json"
        method = "GET"
<<<<<<< Updated upstream
        return self.__generic_api_call(call, method)

############################################################################################
#                                                                                          #
#                                Folder API Calls                                          # 
#                                                                                          #             
############################################################################################
    
    def browse_folders(self, root, offset=None, max_depth=None, max_return=None, workspace=None):
        """
        This method returns a list of folders in Marketo.
        
        Args:
            root (int):                     The id of the parent folder
            offset (int, optional):         Which index inside the parent to start from (default 0)
            max_depth (int, optional):      Maximum levels of recursion (default 2)
            max_return (int, optional):     Maximum folders to returns (default 20, max 200)
            workspace (string, optional):   Which workspace to search in
            
        Returns:
            dict:   The response from the server
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
            folder_id (int):    The id of the folder
            
        Returns:
            dict:   The response from the server
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
            dict:   The response from the server
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
            dict:   The response from the server
        """
        call = "rest/asset/v1/folders.json?name="+name+"&parent="+str(parent)
        method = "POST"
        
        if description is not None:
            call += "&description="+description
            
        return self.__generic_api_call(call, method)
        
    def delete_folder(self, folder_id):
        """
        This method deletes the folder with the given id.
        
        Args:
            folder_id (int):    The id of the folder to be deleted
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/folder/"+str(folder_id)+"/delete.json"
        method = "POST"
        return self.__generic_api_call(call, method)
    
    def update_folder(self, description=None, name=None, isArchive=None):
        pass
        
############################################################################################
#                                                                                          #
#                                  Email API Calls                                         # 
#                                                                                          #             
############################################################################################

    def get_emails(self):
        """
        This method gets a list of all the emails and their metadata
        from the Marketo instance.
        
        Args:
            None
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emails.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_by_id(self, email):
        """
        This method gets an email asset given its id.
        
        Args:
            email (string): The id of the desired email asset
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/email/"+email+".json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_content_by_id(self, email):
        """
        This method gets an email asset's content given its id.
        
        Args:
            email (string): The id of the desired email asset
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/email/"+email+"/content.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_content_by_section_id(self, email, section):
        """
        This method gets a specific section of an email asset's content 
        given both the email and section ids.
        
        Args:
            email (string):     The id of the desired email asset
            section (string):   The id of the desired section
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/email/"+email+"/content/"+section+".json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
############################################################################################
#                                                                                          #
#                             Email Template API Calls                                     # 
#                                                                                          #             
############################################################################################

    def get_email_templates(self):
        """
        This method returns a list of all email templates.
        
        Args:
            None
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplates.json"
        method = "GET"
        return self.__generic_api_call(call, method)

    def get_email_template_by_name(self, template_name):
        """
        This method returns the meta data of the given email template
        
        Args:
            template_name (string):   The name of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/byName.json?name="+template_name
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_template_by_id(self, template_id):
        """
        This method returns the meta data of the given email template
        
        Args:
            template_id (string):   The id of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+".json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def get_email_template_content_by_id(self, template_id):
        """
        This method returns the HTML of the given email template
        
        Args:
            template_id (string):   The id of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/content.json"
        method = "GET"
        return self.__generic_api_call(call, method)
    
    def update_email_template(self, template_id, name=None, description=None):
        """
        This method updates the name and/or description of the given email template
        
        Args:
            template_id (string):             The id of the desired email template
            name (string, optional):          The new name of the email template
            description (string, optional):   The new description of the email template
            
        Returns:
            dict:   The response from the server
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
            template_id (string):   The id of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/approveDraft.json"
        method = "POST"
        return self.__generic_api_call(call, method)      
    
    def unapprove_email_template(self, template_id):
        """
        This method unapproves the given email template
        
        Args:
            template_id (string):   The id of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/unapprove.json"
        method = "POST"
        return self.__generic_api_call(call, method)    
    
    def delete_email_template(self, template_id):
        """
        This method deletes the given email template
        
        Args:
            template_id (string):   The id of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/delete.json"
        method = "POST"
        return self.__generic_api_call(call, method)
    
    def discard_email_template_draft(self, template_id):
        """
        This method discards the draft of the given email template
        
        Args:
            template_id (string):   The id of the desired email template
            
        Returns:
            dict:   The response from the server
        """
        call = "rest/asset/v1/emailTemplate/"+template_id+"/discardDraft.json"
        method = "POST"
        return self.__generic_api_call(call, method)
    
#############################################################################################
# TODO - This is actually fine. It's the dictionary in the API call that is mucking things up
#############################################################################################
    
    def clone_email_template(self, template_id, name, folder):
        """
        This method clones the given email template
        
        Args:
            template_id (string):   The id of the desired email template
            name (string):          The name of the new email template
            folder (string):        The destination folder for the new email template
            
        Returns:
            dict:   The response from the server
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
        
<<<<<<< Updated upstream
#    print(marketo.get_lead_by_id("5"))

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
    print(marketo.get_folder_by_name("Blog"))
