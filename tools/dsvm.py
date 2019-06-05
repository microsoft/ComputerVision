import json
import re
import subprocess
import textwrap
from shutil import which
from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text, HTML


# variables
UBUNTU_DSVM_IMAGE = (
    "microsoft-dsvm:linux-data-science-vm-ubuntu:linuxdsvmubuntu:latest"
)
vm_options = dict(
    gpu=dict(size="Standard_NC6s_v3", family="NCSv3", cores=6),
    cpu=dict(size="Standard_DS3_v2", family="DSv2", cores=4),
)

# list of cmds
account_list_cmd = "az account list -o table"
sub_id_list_cmd = 'az account list --query []."id" -o tsv'
region_list_cmd = 'az account list-locations --query []."name" -o tsv'
silent_login_cmd = 'az login --query "[?n]|[0]"'
set_account_sub_cmd = "az account set -s {}"
provision_rg_cmd = "az group create --name {} --location {}"
provision_vm_cmd = (
    "az vm create --resource-group {} --name {} --size {} --image {} "
    "--admin-username {} --admin-password {} --authentication-type password"
)
vm_ip_cmd = (
    "az vm show -d --resource-group {}-rg --name {} "
    '--query "publicIps" -o json'
)
quota_cmd = (
    "az vm list-usage --location {} --query "
    "[?contains(localName,'{}')].{{max:limit,current:currentValue}}"
)


def is_installed(cli_app: str) -> bool:
    """Check whether `name` is on PATH and marked as executable."""
    return which(cli_app) is not None


def validate_password(password: str) -> bool:
    """ Checks that the password is valid.

    Args:
        password: password string

    Returns: True if valid, else false.
    """

    if len(password) < 12 or len(password) > 123:
        print_formatted_text(
            HTML(
                (
                    "<ansired>Input must be between 12 and 123 characters. "
                    "Please try again.</ansired>"
                )
            )
        )
        return False

    if (
        len([c for c in password if c.islower()]) <= 0
        or len([c for c in password if c.isupper()]) <= 0
    ):
        print_formatted_text(
            HTML(
                (
                    "<ansired>Input must contain a upper and a lower case "
                    "character. Please try again.</ansired>"
                )
            )
        )
        return False

    if len([c for c in password if c.isdigit()]) <= 0:
        print_formatted_text(
            HTML(
                "<ansired>Input must contain a digit. Please try again.</ansired>"
            )
        )
        return False

    if len(re.findall("[\W_]", password)) <= 0:
        print_formatted_text(
            HTML(
                (
                    "<ansired>Input must contain a special character. "
                    "Please try again.</ansired>"
                )
            )
        )
        return False

    return True


def validate_vm_name(vm_name) -> bool:
    """ Checks that the vm name is valid.

    Args:
        vm_name: the name of the vm to check

    Returns: True if valid, else false.
    """
    # we minus 3 for max length because we generate the rg using: "{vm_name}-rg"
    if len(vm_name) < 1 or len(vm_name) > (64 - 3):
        print_formatted_text(
            HTML(
                (
                    f"<ansired>Input must be between 1 and {64-3} characters. "
                    "Please try again.</ansired>"
                )
            )
        )
        return False

    if not bool(re.match("^[A-Za-z0-9-]*$", vm_name)):
        print_formatted_text(
            HTML(
                (
                    "<ansired>You can only use alphanumeric characters and "
                    "hyphens. Please try again.</ansired>"
                )
            )
        )
        return False

    return True


def prompt_subscription_id() -> str:
    """ Prompt for subscription id. """
    subscription_id = None
    subscription_is_valid = False
    results = subprocess.run(
        sub_id_list_cmd.split(" "), stdout=subprocess.PIPE
    )
    subscription_ids = results.stdout.decode("utf-8").strip().split("\n")
    while not subscription_is_valid:
        subscription_id = prompt(
            ("Enter your subscription id " "(copy & paste it from above): ")
        )
        if subscription_id in subscription_ids:
            subscription_is_valid = True
        else:
            print_formatted_text(
                HTML(
                    (
                        "<ansired>The subscription id you entered is not "
                        "valid. Please try again.</ansired>"
                    )
                )
            )
    return subscription_id


def prompt_vm_name() -> str:
    """ Prompt for VM name. """
    vm_name = None
    vm_name_is_valid = False
    while not vm_name_is_valid:
        vm_name = prompt(
            f"Enter a name for your vm (ex. 'cv-datascience-vm'): "
        )
        vm_name_is_valid = validate_vm_name(vm_name)
    return vm_name


def prompt_region() -> str:
    """ Prompt for region. """
    region = None
    region_is_valid = False
    results = subprocess.run(
        region_list_cmd.split(" "), stdout=subprocess.PIPE
    )
    valid_regions = results.stdout.decode("utf-8").strip().split("\n")
    while not region_is_valid:
        region = prompt(f"Enter a region for your vm (ex. 'eastus'): ")
        if region in valid_regions:
            region_is_valid = True
        else:
            print_formatted_text(
                HTML(
                    textwrap.dedent(
                        """\
                        <ansired>The region you entered is invalid. You can run
                        `az account list-locations` to see a list of the valid
                        regions. Please try again.</ansired>\
                        """
                    )
                )
            )
    return region


def prompt_username() -> str:
    """ Prompt username. """
    username = None
    username_is_valid = False
    while not username_is_valid:
        username = prompt("Enter a username: ")
        if len(username) > 0:
            username_is_valid = True
        else:
            print_formatted_text(
                HTML(
                    (
                        "<ansired>Username cannot be empty. "
                        "Please try again.</ansired>"
                    )
                )
            )
    return username


def prompt_password() -> str:
    """ Prompt for password. """
    password = None

    password_is_valid = False
    while not password_is_valid:
        password = prompt("Enter a password: ", is_password=True)
        if not validate_password(password):
            continue

        password_match = prompt(
            "Enter your password again: ", is_password=True
        )
        if password == password_match:
            password_is_valid = True
        else:
            print_formatted_text(
                HTML(
                    (
                        "<ansired>Your passwords do not match. Please try "
                        "again.</ansired>"
                    )
                )
            )

    return password


def prompt_use_gpu() -> str:
    """ Prompt for GPU or CPU. """
    use_gpu = None
    valid_response = False
    while not valid_response:
        use_gpu = prompt(
            (
                "Do you want to use a GPU-enabled VM (It will incur a "
                "higher cost) [y/n]: "
            )
        )
        if use_gpu in ("Y", "y", "N", "n"):
            valid_response = True
        else:
            print_formatted_text(
                HTML("<ansired>Enter 'y' or 'n'. Please try again.</ansired>")
            )
    return True if use_gpu in ("Y", "y") else False


def check_quota(region: str, vm_family: str) -> int:
    """ Checks if the subscription has quote in the specified region.

    Args:
        region: the region to check
        vm_family: the vm family to check

    Returns: the available quota
    """
    results = subprocess.run(
        quota_cmd.format(region, vm_family).split(" "), stdout=subprocess.PIPE
    )
    quota = json.loads("".join(results.stdout.decode("utf-8")))
    return int(quota[0]["max"]) - int(quota[0]["current"])


def create_dsvm() -> None:
    """ Interaction session to create a data science vm. """

    # print intro dialogue
    print_formatted_text(
        HTML(
            textwrap.dedent(
                """
            Azure Data Science Virtual Machine Builder

            This utility will help you create an Azure Data Science Ubuntu Virtual
            Machine that you will be able to run your notebooks in. The VM will
            be based on the Ubuntu DSVM image.

            For more information about Ubuntu DSVMs, see here:
            https://docs.microsoft.com/en-us/azure/machine-learning/data-science-virtual-machine/dsvm-ubuntu-intro

            This utility will let you select a GPU machine or a CPU machine.

            The GPU machine specs:
                - size: Standard_NC6s_v3 (NVIDIA Tesla V100 GPUs)
                - family: NC6s
                - cores: 6

            The CPU machine specs:
                - size: Standard_DS3_v2 (Intel Xeon® E5-2673 v3 2.4 GHz (Haswell))
                - family: DSv2
                - cores: 4

            Pricing information on the SKUs can be found here:
            https://azure.microsoft.com/en-us/pricing/details/virtual-machines

            To use this utility, you must have an Azure subscription which you can
            get from azure.microsoft.com.

            Answer the questions below to setup your machine.

            ------------------------------------------
            """
            )
        )
    )

    # validate active user
    prompt("Press enter to continue...\n")

    # check that az cli is installed
    if not is_installed("az"):
        print(
            textwrap.dedent(
                """\
            You must have the Azure CLI installed. For more information on
            installing the Azure CLI, see here:
            https://docs.microsoft.com/en-us/cli/azure/?view=azure-cli-latest
        """
            )
        )
        exit(0)

    # check if we are logged in
    print("Checking to see if you are already logged in...")
    results = subprocess.run(
        account_list_cmd.split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logged_in = False if results.stderr else True

    # login to the az cli and suppress output
    if not logged_in:
        subprocess.run(silent_login_cmd.split(" "))
        print("\n")
    else:
        print_formatted_text(
            HTML(
                (
                    "<ansigreen>Looks like you're already logged "
                    "in.</ansigreen>\n"
                )
            )
        )

    # show account sub list
    print("Here is a list of your subscriptions:")
    results = subprocess.run(
        account_list_cmd.split(" "), stdout=subprocess.PIPE
    )
    print_formatted_text(
        HTML(f"<ansigreen>{results.stdout.decode('utf-8')}</ansigreen>")
    )

    # prompt fields
    subscription_id = prompt_subscription_id()
    vm_name = prompt_vm_name()
    region = prompt_region()
    use_gpu = prompt_use_gpu()
    username = prompt_username()
    password = prompt_password()

    # set GPU
    vm = vm_options["gpu"] if use_gpu else vm_options["cpu"]

    # check quota
    if check_quota(region, vm["family"]) < vm["cores"]:
        print_formatted_text(
            HTML(
                textwrap.dedent(
                    f"""\
                <ansired>
                The subscription '{subscription_id}' does not have enough
                cores of {vm['family']} in the region: {region}.

                To request more cores:
                https://docs.microsoft.com/en-us/azure/azure-supportability/resource-manager-core-quotas-request

                (If you selected GPU, you may try using CPU instead.)

                Exiting...
                </ansired>\
                """
                )
            )
        )
        exit()

    # set sub id
    subprocess.run(set_account_sub_cmd.format(subscription_id).split(" "))

    # provision rg
    print_formatted_text(
        HTML(("\n<ansiyellow>Creating the resource group.</ansiyellow>"))
    )
    results = subprocess.run(
        provision_rg_cmd.format(f"{vm_name}-rg", region).split(" "),
        stdout=subprocess.PIPE,
    )
    if "Succeeded" in results.stdout.decode("utf-8"):
        print_formatted_text(
            HTML(
                (
                    "<ansigreen>Your resource group was "
                    "successfully created.</ansigreen>\n"
                )
            )
        )

    # create vm
    print_formatted_text(
        HTML(
            (
                "<ansiyellow>Creating the Data Science VM. "
                "This may take up a few minutes...</ansiyellow>"
            )
        )
    )
    results = subprocess.run(
        provision_vm_cmd.format(
            f"{vm_name}-rg",
            vm_name,
            vm["size"],
            UBUNTU_DSVM_IMAGE,
            username,
            password,
        ).split(" "),
        stdout=subprocess.PIPE,
    )

    # get vm ip
    results = subprocess.run(
        vm_ip_cmd.format(vm_name, vm_name).split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if len(results.stderr.decode("utf-8")) > 0:
        exit()
    vm_ip = results.stdout.decode("utf-8").strip().strip('"')
    if len(vm_ip) > 0:
        print_formatted_text(
            HTML("<ansigreen>VM creation succeeded.</ansigreen>\n")
        )

    # exit message
    print_formatted_text(
        HTML(
            textwrap.dedent(
                f"""
            DSVM creation is complete. We recommend saving the details below.
            <ansiyellow>
            VM information:
                - vm_name:         {vm_name}
                - ip:              {vm_ip}
                - region:          {region}
                - username:        {username}
                - password:        ****
                - resource_group:  {vm_name}-rg
                - subscription_id: {subscription_id}
            </ansiyellow>
            To start/stop VM:
            <ansiyellow>
                $az vm stop -g {vm_name}-rg -n {vm_name}
                $az vm start -g {vm_name}-rg -n {vm_name}
            </ansiyellow>
            To connect via ssh and tunnel:
            <ansiyellow>
                $ssh -L 8000:localhost:8000 {username}@{vm_ip}
            </ansiyellow>
            To delete the VM (this command is unrecoverable):
            <ansiyellow>
                $az group delete -n {vm_name}-rg
            </ansiyellow>
            Please remember that virtual machines will incur a cost on your
            Azure subscription. Remember to stop your machine if you are not
            using it to minimize the cost.\
            """
            )
        )
    )


if __name__ == "__main__":
    create_dsvm()
