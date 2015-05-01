__author__ = "Andrew Garcia <angarcia@marketo.com>"

# TODO: What if the field doesn't exist?

class FieldMapper:
    """
    This class is for mapping MongoDB fields to the Marketo API fields.
    
    Attributes:
        __field_mappings (dict):    This is a static field mapping dictionary that maps MongoDB fields (left)
                                    to the Marketo API field names (right). This needs to be updated any time 
                                    that more fields are added to MongoDB. To use it, input the MongoDB field
                                    name as the key, and it will return the Marketo API name as the value. 
                                    E.G. __field_mappings[<mongoDBfield>] returns the Marketo API equivalent
                                    of <mongoDBfield>
        __input (dict):             A dictionary of key/value pairs whose keys need to be mapped according
                                    to the specification in __field_mappings
        __output (dict):            A dictionary with identical values to __input, but with the appropriate
                                    keys according to __field_mappings
    """
    
############################################################################################
#                                                                                          #
#                                   Constructor                                            # 
#                                                                                          #             
############################################################################################

    def __init__(self):
        """
        As part of initialization, the object runs the map_fields() method, which 
        creates the __output dictionary. The map can then be retrieved with getOutput()
        
        Args:
            table (dict):   A dictionary containing all of the key/value pairs from 
                            MongoDB. This would typically come from the Cursor object
                            returned from get_table() in mongo_wrapper.py
        """
        self.__field_mappings = {
        "First_Name":       "firstName",
        "Last_Name":        "lastName",
        "Email":            "email",
        "Office_Phone":     "phone",
        "Cell_Phone":       "mobilePhone",
        "Company":          "company",
        "Address":          "address",
        "City":             "city",
        "Zip":              "postalCode",
        "Num_Products":     "numProductsOwned",
        "Custom_Field":     "customField"
        }

############################################################################################
#                                                                                          #
#                                        Methods                                           # 
#                                                                                          #             
############################################################################################

    def map_field(self, field):        
        """
        This function returns the Marketo API equivalent of a MongoDB field
        
        Args:
            field (string):    The field inside of the __input dictionary to map
            
        Returns: 
            string: The Marketo API equivalent of the 'field' argument
        """
        # All it does is lookup 'field' in the mapping dictionary and return the
        # mapped value
        return self.__field_mappings[field] 
    
    def map_fields(self, inp):
        """
        This function loops through a dictionary and returns a new dictionary with
        all of the fields mapped.
        
        Args:
            inp (dictionary):   A dictionary containing MongoDB fields
            
        Returns: 
            dictionary:     A dictionary containing Marketo API fields with the same
                            values as the original MongoDB dictionary
        """
        mapping = {}
        for key in inp:
            # MongoDB adds a strange field called '_id' that is impossible to work with (strange object type).
            # Even though it was not part of our data set, it was created anyways. I think it 
            # is because a unique identifier was not specified when the data were imported, so MongoDB
            # created one. Anyways, it's not needed, so it is ignored here.
            if key == "_id":
                pass
            else:
                mapping[self.map_field(key)] = inp[key]
        return mapping