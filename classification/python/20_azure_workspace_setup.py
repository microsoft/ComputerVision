#!/usr/bin/env python
# coding: utf-8

# <i>Copyright (c) Microsoft Corporation. All rights reserved.</i>
#
# <i>Licensed under the MIT License.</i>
#
# # Setup of an Azure workspace

# ## 1. Introduction <a id="intro"></a>
#
# This notebook is the first of a series (starting with "2x_") that leverage the [Azure Machine Learning Service](https://docs.microsoft.com/en-us/azure/machine-learning/service/overview-what-is-azure-ml). Azure ML, as we also call it, is a service that allows us to train, deploy, automate, and manage machine learning models, at scale, in the cloud.
#
# In this tutorial, we will set up an [Azure ML workspace](https://docs.microsoft.com/en-us/azure/machine-learning/service/concept-azure-machine-learning-architecture#workspace). Such resource organizes and coordinates the actions of many other Azure resources to assist in executing and sharing machine learning workflows. In particular, an Azure ML Workspace coordinates storage, databases, and compute resources providing added functionality for machine learning experimentation, deployment, inferencing, and the monitoring of deployed models.
#
# ## 2. Pre-requisites
# <a id="pre-reqs"></a>
#
# For this and all the other "2x_" notebooks to run properly on our machine, we need access to the Azure platform.
#
# Unless we already have one, we should first:
# - [Create an account](https://azure.microsoft.com/en-us/free/services/machine-learning/)
# - [Create a resource group and a workspace](https://docs.microsoft.com/en-us/azure/machine-learning/service/setup-create-workspace#portal).

# ## 3. Azure workspace <a id="workspace"></a>
#
# In the deployment tutorials present in this repository (numbered "21_" to "25_"), we use the Azure ML SDK. It allows us to access our Azure resources programmatically. As we are running our notebooks in the "cvbp" conda environment, the SDK should already be installed on our machine. Let's check which version of the Azure SDK we are working with.

# In[ ]:


# For automatic reloading of modified libraries
get_ipython().run_line_magic("reload_ext", "autoreload")
get_ipython().run_line_magic("autoreload", "2")

# Azure
import azureml.core
from azureml.core import Workspace
from azureml.exceptions import ProjectSystemException, UserErrorException

# Check core SDK version number
print(f"Azure ML SDK Version: {azureml.core.VERSION}")


# We are now ready to load an existing workspace, or create a new one and save it to a local configuration file (`./aml_config/config.json`). This will give us access to the workspace object (`ws`).
#
# We are typically in one of the following cases:
# 1. We created our workspace from the Azure portal, as explained in the link above
# 2. We created a workspace from a script or notebook and already have a `config.json` file
# 3. We created a workspace from a script or notebook and, for any reason, don't have such a file
# 4. We already have one (or several) workspace, but don't want to use that one here
# 5. We do not have any workspace at all
#
# In cases 1 through 3, our workspace already exists, and we just need to load it. We do so either from the local configuration file (using `Worspace.from_config()`), if we have it, or directly from Azure (through `Workspace.create(exists_ok=True)`).
#
# For cases 4 and 5, we need to create a brand new workspace.
#
# Whether we retrieve an existing workspace from Azure or create a new one, we need to save its configuration into the `config.json` file, using `ws.write_config()`. This will be useful in the following deployment notebooks.
#
# In all cases, except #2, we need to provide 4 pieces of information:
# - <b>subscription ID:</b> the ID of the Azure subscription we are using
# - <b>resource group:</b> the name of the resource group in which our workspace resides
# - <b>workspace region:</b> the geographical area in which our workspace resides (e.g. "eastus2" -- other examples are available [here](https://azure.microsoft.com/en-us/global-infrastructure/geographies/) <i>-- note the lack of spaces</i>)
# - <b>workspace name:</b> the name of the workspace we want to create or retrieve.
#
# For case #2, we can comment the 4 next lines out.

# In[ ]:


# Let's define these variables here - These pieces of information can be found on the portal
subscription_id = os.getenv("SUBSCRIPTION_ID", default="<our_subscription_id>")
resource_group = os.getenv("RESOURCE_GROUP", default="<our_resource_group>")
workspace_name = os.getenv("WORKSPACE_NAME", default="<our_workspace_name>")
workspace_region = os.getenv(
    "WORKSPACE_REGION", default="<our_workspace_region>"
)

try:
    # Let's load the workspace from the configuration file
    ws = Workspace.from_config()
    print("Workspace was loaded successfully from the configuration file")
except (UserErrorException, ProjectSystemException):
    # or directly from Azure, if it already exists (exist_ok=True).
    # If it does not exist, let's create a workspace from scratch
    ws = Workspace.create(
        name=workspace_name,
        subscription_id=subscription_id,
        resource_group=resource_group,
        location=workspace_region,
        create_resource_group=True,
        exist_ok=True,
    )
    ws.write_config()
    print("Workspace was loaded successfully from Azure")


# Let's check that the workspace is properly loaded

# In[ ]:


# Print the workspace attributes
print(
    f"Workspace name: {ws.name}\n       Workspace region: {ws.location}\n       Subscription id: {ws.subscription_id}\n       Resource group: {ws.resource_group}"
)


# We can also see this workspace on the [Azure portal](http://portal.azure.com) by sequentially clicking on:
# - Resource groups, and clicking the one we referenced above

# <img src="media/resource_group.jpg" width="800" alt="Azure portal view of resource group">

# - Workspace_name

# <img src="media/workspace.jpg" width="800" alt="Azure portal view of workspace">

# For more details on the setup of a workspace and other Azure resources, we can refer to this [configuration](https://github.com/Azure/MachineLearningNotebooks/blob/dcce6f227f9ca62e4c201fb48ae9dc8739eaedf7/configuration.ipynb) notebook.
#
# Creating a workspace automatically adds associated resources:
# - A container registry, which can host Docker images, and gets lazily created
# - A storage account, in which output files get stored
# - Application Insights, which allows us to monitor the health of and traffic to a web service, for instance
# - A key vault, which stores our credentials.
#
# Such resources, when first created, cost less than a penny per day. To get a better sense of pricing, we can refer to this [calculator](https://azure.microsoft.com/en-us/pricing/calculator/). We can also navigate to the [Cost Management + Billing](https://ms.portal.azure.com/#blade/Microsoft_Azure_Billing/ModernBillingMenuBlade/Overview) pane on the portal, click on our subscription ID, and click on the Cost Analysis tab to check our credit usage.
#
# We will continue using our workspace in the next notebooks, so will keep it available. However, if we needed to delete it, we would run the command below.

# In[ ]:


# ws.delete(delete_dependent_resources=True)
# This deletes our workspace, the container registry, the account storage, Application Insights and the key vault


# ## 4. Next steps <a id="next-step"></a>
#
# In this notebook, we loaded or created a new workspace, and stored configuration information in a `./aml_config/config.json` file. This is the file we will use in all the Azure ML-related notebooks in this repository. There, we will only need `ws = Workspace.from_config()`.
#
# In the next notebook, we will learn how to deploy a trained model as a web service on Azure.
